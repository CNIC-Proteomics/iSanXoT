from typing import cast, Any, Awaitable, Callable, Generic, TypeVar
import asyncio
import functools

from .pipe import pipe, PipeEnd, ConcurrentPipeEnd


__all__ = [
    'Component',
    'component_coro_wrapper',
    'component_workload',
    'start_component',
    'start_component_in_thread',
]


T = TypeVar('T')
CoroutineFunction = Callable[..., Awaitable[T]]


# TODO asyncio.Future is not generic, but Awaitable[T] doesn't have cancel()
_Future = Awaitable[T]


class Component(Generic[T]):
    """\
    A component is a connection to a workload executed somewhere else.
    Two pipes and a future are used for communication:
    `commands` is for owner-initiated communication, `events` for task-initiated communication,
    and the future is used to cancel the workload or get its result.
    Replies to commands are sent task-to-owner on the command pipe,
    and replies to events are sent owner-to-task on the event pipe;
    the reserved event `Component.EVENT_START` and command `Component.COMMAND_STOP` do not expect a reply.

    The workload is required to show the following behavior:

    - it must send `Component.EVENT_START` to its owner after the task is initialized;
    - it must send EOF on the event pipe before terminating, and not earlier;
    - it should wrap any raised exception in `Component.Failure`,
      or raise `Component.LifecycleError` for violations of this contract;
    - when `Component.COMMAND_STOP` is received, it should either stop eventually, or send an event to its owner;
    - when the future is cancelled, it should either stop eventually, or send an event to its owner.

    The latter three are soft requirements, with the last two only ruling out the workload running forever
    without ever sending an event after a stop/cancellation request.
    A workload may choose to ignore stop commands or cancellations, but should document if it does.
    """

    class LifecycleError(RuntimeError): pass
    class Success(Exception): pass
    class Failure(Exception): pass
    class EventException(Exception): pass

    EVENT_START = 'EVENT_START'
    COMMAND_STOP = 'COMMAND_STOP'

    def __init__(self, commands: PipeEnd, events: PipeEnd, future: _Future[T]) -> None:
        self._commands = commands
        self._events = events
        self._future = future

    async def wait_for_start(self) -> None:
        """\
        Start the component. This waits for `Component.EVENT_START` to be sent from the task.
        If the task returns without an event, a `LifecycleError` is raised with a `Success` as its cause.
        If the task raises an exception before any event, that exception is raised.
        If the task sends a different event than `Component.EVENT_START`,
        the task is cancelled (without waiting for the task to shut down) and a `LifecycleError` is raised.
        """
        try:
            start_event = await self.recv_event()
        except Component.Success as succ:
            raise Component.LifecycleError(f"component returned before start finished") from succ
        except Component.Failure as fail:
            # here we don't expect a wrapped result, so we unwrap the failure
            cause, = fail.args
            raise cause from None
        else:
            if start_event != Component.EVENT_START:
                self.cancel_nowait()
                raise Component.LifecycleError(f"Component must emit EVENT_START, was {start_event}")

    async def stop_nowait(self) -> None:
        """\
        Stop the component; sends `Component.COMMAND_STOP` to the task.
        Stopping requires the component to receive the command and actively comply with it.
        It is a clean method of shutdown, but requires active cooperation.
        This method may block on sending the command, but will not wait for the component to shut down.
        """
        await self.send(Component.COMMAND_STOP)

    async def stop(self) -> T:
        """\
        Stop the component; calls `stop_nowait()` and returns `result()`.
        """
        await self.stop_nowait()
        return await self.result()

    def cancel_nowait(self) -> None:
        """\
        Cancel the component.
        Cancelling raises a `CancelledError` into the task, which will normally terminate it.
        It is a forced method of shutdown, and only requires the component to not actively ignore cancellations.
        """
        cast(asyncio.Future, self._future).cancel()

    async def cancel(self) -> T:
        """\
        Cancel the component; calls `cancel_nowait()` and returns `result()`.
        """
        self.cancel_nowait()
        return await self.result()

    async def result(self) -> T:
        """\
        Wait for the task's termination; either the result is returned or a raised exception is reraised.
        If an event is sent before the task terminates, an `EventException` is raised with the event as argument.
        """
        try:
            event = await self.recv_event()
        except Component.Success as succ:
            # success was thrown; return the result
            result, = succ.args
            return cast(T, result)
        except Component.Failure as fail:
            # here we don't expect a wrapped result, so we unwrap the failure
            cause, = fail.args
            raise cause
        else:
            # there was a regular event; shouldn't happen/is exceptional
            raise Component.EventException(event)

    async def send(self, value: Any) -> None:
        """\
        Sends a command to the task.
        """
        await self._commands.send(value)

    async def recv(self) -> Any:
        """\
        Receives a command reply from the task.
        """
        return await self._commands.recv()

    async def request(self, value: Any) -> Any:
        """\
        Sends a command to and receives the reply from the task.
        """
        await self.send(value)
        return await self.recv()

    async def recv_event(self) -> Any:
        """\
        Receives an event from the task.
        If the task terminates before another event, an exception is raised.
        A normal return is wrapped in a `Success` exception,
        other exceptions result in a `Failure` with the original exception as the cause.
        """
        try:
            return await self._events.recv()
        except EOFError:
            # component has terminated, raise the cause (either Failure, or LifecycleError) or Success
            raise Component.Success(await self._future)

    async def send_event_reply(self, value: Any) -> None:
        """\
        Sends a reply for an event received from the task.
        """
        await self._events.send(value)


async def component_coro_wrapper(coro_func: CoroutineFunction[T],
                                 *args: Any, commands: PipeEnd, events: PipeEnd, **kwargs: Any) -> T:
    """\
    This function wraps a component workload to conform to the required lifecycle.
    The following behavior is the passed coroutine function's responsibility:

    - it must send `Component.EVENT_START` to its owner after the task is initialized;
    - it must not send EOF on the event pipe;
    - when `Component.COMMAND_STOP` is received, it should either stop eventually, or send an event to its owner;
    - when it is cancelled, it should either stop eventually, or send an event to its owner.

    Also, any `Component.LifecycleError` raised will be wrapped in `Component.Failure`.
    """
    try:
        return await coro_func(*args, commands=commands, events=events, **kwargs)
    except Exception as err:
        raise Component.Failure(err) from None
    finally:
        try:
            await events.send(eof=True)
        except EOFError as err:
            raise Component.LifecycleError("component closed events pipe manually") from err


def component_workload(coro_func: CoroutineFunction[T]) -> CoroutineFunction[T]:
    """\
    A decorator that wraps the decorated function into `component_coro_wrapper`.
    Note that decorated functions can not be pickled,
    so this can't be used directly for workloads being sent to different processes.
    As a workaround, instead decorate a nested function:

        async def workload(*args, commands, events, **kwargs):
            @component_workload
            async def _workload(*args, commands, events, **kwargs):
                # initialize
                await events.send(Component.EVENT_START)
                # do some work

            await _workload(*args, commands, events, **kwargs)
    """
    return functools.partial(component_coro_wrapper, coro_func)


async def start_component(workload: CoroutineFunction[T], *args: Any, **kwargs: Any) -> Component[T]:
    """\
    Starts the passed `workload` with additional `commands` and `events` pipes.
    The workload will be executed as a task.

    A simple example. Note that here, the component is exclusively reacting to commands,
    and the owner waits for acknowledgements to its commands, making the order of outputs predictable.

    >>> @component_workload
    ... async def component(msg, *, commands, events):
    ...     # do any startup tasks here
    ...     print("> component starting up...")
    ...     await events.send(Component.EVENT_START)
    ...
    ...     count = 0
    ...     while True:
    ...         command = await commands.recv()
    ...         if command == Component.COMMAND_STOP:
    ...             # honor stop commands
    ...             break
    ...         elif command == 'ECHO':
    ...             print(f"> {msg}")
    ...             count += 1
    ...             # acknowledge the command was serviced completely
    ...             await commands.send(None)
    ...         else:
    ...             # unknown command; terminate
    ...             # by closing the commands pipe,
    ...             # the caller (if waiting for a reply) will receive an EOFError
    ...             await commands.send(eof=True)
    ...             raise ValueError
    ...
    ...     # do any cleanup tasks here, probably in a finally block
    ...     print("> component cleaning up...")
    ...     return count
    ...
    >>> async def example():
    ...     print("call start")
    ...     comp = await start_component(component, "Hello World")
    ...     print("done")
    ...
    ...     print("send command")
    ...     await comp.request('ECHO')
    ...     print("done")
    ...
    ...     print("call stop")
    ...     count = await comp.stop()
    ...     print("done")
    ...
    ...     print(count)
    ...
    >>> asyncio.run(example())
    call start
    > component starting up...
    done
    send command
    > Hello World
    done
    call stop
    > component cleaning up...
    done
    1
    """

    commands_a, commands_b = pipe()
    events_a, events_b = pipe()

    task = asyncio.create_task(workload(*args, commands=commands_b, events=events_b, **kwargs))

    component = Component[T](commands_a, events_a, task)
    await component.wait_for_start()
    return component


async def start_component_in_thread(executor, workload: CoroutineFunction[T], *args: Any, loop=None, **kwargs: Any) -> Component[T]:
    """\
    Starts the passed `workload` with additional `commands` and `events` pipes.
    The workload will be executed on an event loop in a new thread; the thread is provided by `executor`.

    This function is not compatible with `ProcessPoolExecutor`,
    as references between the workload and component are necessary.

    Be careful when using an executor with a maximum number of threads,
    as long running workloads may starve other tasks.
    Consider using a dedicated executor that can spawn at least as many threads
    as concurrent long-running tasks are expected.
    """

    loop = loop or asyncio.get_event_loop()

    commands_a, commands_b = pipe(loop=loop)
    events_a, events_b = pipe(loop=loop)

    commands_b = ConcurrentPipeEnd(commands_b, loop=loop)
    events_b = ConcurrentPipeEnd(events_b, loop=loop)

    _workload = workload(*args, commands=commands_b, events=events_b, **kwargs)
    future = cast(_Future[T], loop.run_in_executor(executor, asyncio.run, _workload))

    component = Component[T](commands_a, events_a, future)
    await component.wait_for_start()
    return component


try:
    import zmq.asyncio
    from .pipe import zmq_tcp_pipe_end
except:  # pragma: nocover
    pass
else:
    __all__ += [
        'start_component_in_process',
        'start_external_component',
        'StarterFunction',
    ]

    StarterFunction = Callable[[int, int], Awaitable[_Future[T]]]


    # we need a top level function wrapper that can be pickled for transfer to the new process
    def _process_workload_wrapper(workload: CoroutineFunction[T], *args: Any, commands_port: int, events_port: int, **kwargs: Any) -> T:
        async def _workload() -> T:
            ctx = zmq.asyncio.Context()
            commands = await zmq_tcp_pipe_end(ctx, 'b', port=commands_port)
            events = await zmq_tcp_pipe_end(ctx, 'b', port=events_port)

            return await workload(*args, commands=commands, events=events, **kwargs)

        return asyncio.run(_workload())


    async def start_component_in_process(executor, ctx, workload: CoroutineFunction[T], *args: Any, loop=None, **kwargs: Any) -> Component[T]:
        """\
        Starts the passed `workload` with additional `commands` and `events` pipes.
        The workload will be executed on an event loop in a new process; the process is provided by `executor`.

        This function connects component and workload via TCP.
        The coroutine function `workload` and the provided `args` and `kwargs` are transfered to the worker process,
        which means that pickling them must generally be possible.

        Be careful when using an executor with a maximum number of processes,
        as long running workloads may starve other tasks.
        Consider using a dedicated executor that can spawn at least as many threads
        as concurrent long-running tasks are expected.
        """

        loop = loop or asyncio.get_event_loop()

        async def starter(commands_port: int, events_port: int) -> _Future[T]:
            _workload = functools.partial(_process_workload_wrapper, workload, *args,
                                          commands_port=commands_port, events_port=events_port, **kwargs)
            return cast(_Future[T], loop.run_in_executor(executor, _workload))

        return await start_external_component(ctx, starter)


    async def start_external_component(ctx, starter: StarterFunction) -> Component[T]:
        """\
        Given a function with the following signature:

            async def starter(commands_port: int, events_port: int) -> asyncio.Future: ...

        creates new component.

        This function first creates two `zmq_zmq_tcp_pipe_end` of type `'a'`.
        The `starter` function is then called and awaited; its job is to start the workload which must eventually
        connect to the pipe ends, of which the ports are given.
        The return value of `starter` is a future that can be used to cancel the workload,
        or to retrieve its result, including a raised exception.
        """

        ctx = ctx or zmq.asyncio.Context()
        commands = await zmq_tcp_pipe_end(ctx, 'a', initialize=False)
        events = await zmq_tcp_pipe_end(ctx, 'a', initialize=False)
        future = await starter(commands.port, events.port)
        await commands.initialize()
        await events.initialize()

        component = Component[T](commands, events, future)
        await component.wait_for_start()
        return component
