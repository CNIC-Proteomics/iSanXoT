from abc import abstractmethod
from typing import cast, Any, Optional, Sequence, Tuple
import asyncio
import asyncio.locks
import random

from .serializers import Serializer, Pickle


__all__ = [
    'PipeEnd',
    'Pipe',
    'pipe',
    'ConcurrentPipeEnd',
]


class PipeEnd:
    _none = object()

    @staticmethod
    def check_send_args(value: Any, *, eof: bool) -> None:
        if value is PipeEnd._none and not eof:
            raise ValueError("Missing value or EOF")
        if value is not PipeEnd._none and eof:
            raise ValueError("value and EOF are mutually exclusive")

    @abstractmethod
    def send_nowait(self, value: Any=_none, *, eof=False) -> None:
        raise NotImplemented

    @abstractmethod
    async def send(self, value: Any=_none, *, eof=False) -> None:
        raise NotImplemented

    @abstractmethod
    async def recv(self) -> Any:
        raise NotImplemented

    async def request_sendnowait(self, value: Any) -> Any:
        self.send_nowait(value)
        return await self.recv()

    async def request(self, value: Any) -> Any:
        await self.send(value)
        return await self.recv()


Pipe = Tuple[PipeEnd, PipeEnd]


def pipe(maxsize=0, *, loop=None) -> Pipe:
    """\
    A bidirectional pipe of Python objects.

    >>> async def example1():
    ...     a, b = pipe()
    ...     a.send_nowait('foo')
    ...     print(await b.recv())
    >>> asyncio.run(example1())
    foo
    >>> async def example2():
    ...     a, b = pipe()
    ...     await b.send(eof=True)
    ...     await a.recv()
    >>> asyncio.run(example2())
    Traceback (most recent call last):
      ...
    EOFError
    """

    class QueueStream:
        def __init__(self, maxsize=0, *, loop=None) -> None:
            self._queue: asyncio.Queue = asyncio.Queue(maxsize, loop=loop)
            self._eof = asyncio.locks.Event(loop=loop)

        def _check_send(self, value: Any, *, eof: bool) -> None:
            if self._eof.is_set():
                raise EOFError("Cannot send after EOF")
            PipeEnd.check_send_args(value, eof=eof)

        def send_nowait(self, value: Any, *, eof: bool) -> None:
            self._check_send(value, eof=eof)

            if eof:
                self._eof.set()
            else:
                self._queue.put_nowait(value)

        async def send(self, value: Any, *, eof: bool) -> None:
            self._check_send(value, eof=eof)

            if eof:
                self._eof.set()
            else:
                await self._queue.put(value)

        async def recv(self) -> Any:
            get = asyncio.create_task(self._queue.get())
            eof = asyncio.create_task(self._eof.wait())

            done, pending = await asyncio.wait([get, eof], return_when=asyncio.FIRST_COMPLETED)

            # cancel get or eof, whichever is not finished
            for task in pending:
                task.cancel()

            if get in done:
                return get.result()
            else:
                raise EOFError

    class _PipeEnd(PipeEnd):
        def __init__(self, send: QueueStream, recv: QueueStream) -> None:
            super().__init__()
            self._send = send
            self._recv = recv

        def send_nowait(self, value: Any=PipeEnd._none, *, eof=False):
            self._send.send_nowait(value, eof=eof)

        async def send(self, value: Any=PipeEnd._none, *, eof=False):
            await self._send.send(value, eof=eof)

        async def recv(self)-> Any:
            return await self._recv.recv()

    a, b = QueueStream(maxsize, loop=loop), QueueStream(maxsize, loop=loop)
    return _PipeEnd(a, b), _PipeEnd(b, a)


class ConcurrentPipeEnd(PipeEnd):
    """
    Wraps a PipeEnd so that its async functions can be called from a different event loop.
    The synchronous `send_nowait` method as well as `request_sendnowait` are not supported.

    The `loop` to which the PipeEnd originally belongs must be given, as any async calls are
    scheduled onto that loop.
    Multiprocessing is not supported, as access to the actual event loop is required.
    Objects are transferred by reference; they are not pickled or otherwise serialized.
    """

    def __init__(self, pipe_end: PipeEnd, *, loop) -> None:
        super().__init__()
        self._pipe_end = pipe_end
        self._loop = loop

    async def _run(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return await asyncio.wrap_future(future)

    def send_nowait(self, value: Any=PipeEnd._none, *, eof=False) -> None:
        raise NotImplemented

    async def send(self, value=PipeEnd._none, *, eof=False) -> None:
        await self._run(self._pipe_end.send(value, eof=eof))

    async def recv(self) -> Any:
        return await self._run(self._pipe_end.recv())


try:
    import zmq
except:  # pragma: nocover
    pass
else:
    __all__ += [
        'ZmqPipeEnd',
        'zmq_tcp_pipe_end',
        'zmq_tcp_pipe',
        'zmq_ipc_pipe_end',
        'zmq_ipc_pipe',
        'zmq_inproc_pipe_end',
        'zmq_inproc_pipe',
    ]


    class ZmqPipeEnd(PipeEnd):
        """
        A PipeEnd backed by an asynchronous ZMQ socket.
        This PipeEnd can be used for multiprocessing; it will serialize objects that are transmitted.
        The default serialization mechanism is pickle, which can be customized by providing a `Serializer`
        or by overriding the `_serialize` and `_deserialize` methods.
        The synchronous `send_nowait` method and `request_sendnowait` are not supported.

        The sockets connected can be either `DEALER` and `ROUTER` or `PAIR` and `PAIR`.
        Additional sockets must not be connected to the used endpoints.
        For `DEALER`/`ROUTER` connections, the `initialize` method must be called to tell the `ROUTER` socket
        the `DEALER`'s identity.
        Care must be taken when creating both pipe ends synchronously:
        `initialize` will block before the sockets established a connection, i.e. this will cause a deadlock:

        - create & initialize pipe end `'a'`
        - create & initialize pipe end `'b'`

        instead the following is necessary:

        - create pipe ends `'a'` & `'b'`
        - initialize pipe ends `'a'` & `'b'`

        For `PAIR`/`PAIR` connections, `initialize` must not be called.
        `PAIR`/`PAIR` connections are a little more efficient in terms of framing,
        but should only be used over the `inproc` transport, as recommended by ZeroMQ.
        """

        def __init__(self, ctx, socket_type, address: str, *, port: Optional[int], bind=False, serializer: Optional[Serializer]=None) -> None:
            """\
            Creates a ZMQ-socket based pipe end; see the parameters on how a connection is established.
            For `DEALER` and `ROUTER` sockets, `initialize` must be called before the pipe end is complete.

            A `port` of `0` is only valid if `bind` is `True`,
            in which case `bind_to_random_port(address)` will be used for binding.

            After creation, the `port` and `endpoint` properties will contain the ultimately used values.

            :param ctx: the async ZMQ context to get sockets from
            :param socket_type: the socket type; one of `DEALER`, `ROUTER`, `PAIR`
            :param address: the ZMQ endpoint address; without port for the TCP transport
            :param port: the TCP port to use or zero to bind to a random port; `None` for non-TCP transports
            :param bind: whether to bind or to connect the socket to the given address; defaults to `False` (connect)
            :param serializer: the serializer used to pack values into ZMQ messages; defaults to `serializers.Pickle`
            """

            super().__init__()
            if socket_type not in {zmq.DEALER, zmq.ROUTER, zmq.PAIR}:
                raise ValueError("DEALER, ROUTER, or PAIR socket type required")

            self._sock = ctx.socket(socket_type)
            self._socket_type = socket_type
            if bind:
                if port is None:
                    endpoint = address
                    self._sock.bind(endpoint)
                elif port == 0:
                    port = self._sock.bind_to_random_port(address)
                    endpoint = f'{address}:{port}'
                else:
                    endpoint = f'{address}:{port}'
                    self._sock.bind(endpoint)
            else:
                if port is None:
                    endpoint = address
                    self._sock.connect(address)
                else:
                    endpoint = f'{address}:{port}'
                    self._sock.connect(endpoint)
            self.port = port
            self.endpoint = endpoint
            self._dealer_ident: Optional[bytes] = None

            self._serializer: Serializer = serializer or Pickle()
            self._eof_sent = False
            self._eof_recvd = False

        async def initialize(self) -> None:
            """\
            Initializes a `DEALER`/`ROUTER` based connection.
            The DEALER side will send a `[b'']` message;
            the router side will receive it and store the received identifier for sending messages later.
            """

            if self._socket_type == zmq.ROUTER:
                self._dealer_ident, _ = await self._sock.recv_multipart()
            elif self._socket_type == zmq.DEALER:
                await self._sock.send_multipart([b''])
            else:
                raise RuntimeError("initialize() not necessary for PAIR sockets")

        async def _send(self, *parts: bytes) -> None:
            if self._socket_type == zmq.ROUTER:
                parts = (cast(bytes, self._dealer_ident), *parts)
            await self._sock.send_multipart(parts)

        async def _recv(self) -> Sequence[bytes]:
            parts: Sequence[bytes] = await self._sock.recv_multipart()
            if self._socket_type == zmq.ROUTER:
                parts = parts[1:]
            return parts

        def _serialize(self, value: Any) -> bytes:
            return self._serializer.serialize(value)

        def _deserialize(self, msg: bytes) -> Any:
            return self._serializer.deserialize(msg)

        def send_nowait(self, value: Any = PipeEnd._none, *, eof=False) -> None:
            raise NotImplemented

        async def send(self, value: Any=PipeEnd._none, *, eof=False) -> None:
            if self._eof_sent:
                raise EOFError("Cannot send after EOF")
            PipeEnd.check_send_args(value, eof=eof)

            if eof:
                await self._send(b'')
                self._eof_sent = True
            else:
                msg = self._serialize(value)
                await self._send(b'', msg)

        async def recv(self) -> Any:
            if self._eof_recvd:
                raise EOFError("Cannot receive after EOF")

            parts = await self._recv()
            if len(parts) == 1:
                self._eof_recvd = True
                raise EOFError
            else:
                _, msg = parts
                return self._deserialize(msg)


    async def zmq_tcp_pipe_end(ctx, side, *, host=None, port=0, serializer: Optional[Serializer]=None, initialize=True):
        """
        Returns a `ZmqPipeEnd` backed by a TCP connection.
        If both ends of the connection are created on the same thread/task, to avoid a deadlock,
        it's necessary to first create both ends, then initialize `'b'` then `'a'`, such as this:

            a = await zmq_tcp_pipe_end(ctx, 'a', port=port, initialize=False)
            b = await zmq_tcp_pipe_end(ctx, 'b', port=a.port)
            await a.initialize()

        In that case, prefer `zmq_tcp_pipe` for creating both ends.

        Side `'a'` will bind a `ROUTER` socket on the given or a random port (host defaults to `*`);
        side `'b'` will connect a `DEALER` socket to the given port (host defaults to `127.0.0.1`).
        """

        if side == 'a':
            host = host or '*'
            result = ZmqPipeEnd(ctx, zmq.ROUTER, f'tcp://{host}', port=port, bind=True, serializer=serializer)
        elif side == 'b':
            host = host or '127.0.0.1'
            if port == 0:
                raise ValueError("b side requires port argument")
            result = ZmqPipeEnd(ctx, zmq.DEALER, f'tcp://{host}', port=port, serializer=serializer)
        else:
            raise ValueError("side must be 'a' or 'b'")

        if initialize:
            await result.initialize()
        return result


    async def zmq_tcp_pipe(ctx, *, port=0, serializer: Optional[Serializer]=None):
        a = await zmq_tcp_pipe_end(ctx, 'a', port=port, serializer=serializer, initialize=False)
        b = await zmq_tcp_pipe_end(ctx, 'b', port=a.port, serializer=serializer)
        await a.initialize()
        return a, b


    async def zmq_ipc_pipe_end(ctx, side, endpoint, *, serializer: Optional[Serializer]=None, initialize=True):
        """
        Returns a `ZmqPipeEnd` backed by an `ipc` connection; the endpoint must contain the scheme part.
        If both ends of the connection are created on the same thread/task, to avoid a deadlock,
        it's necessary to first create both ends, then initialize `'b'` then `'a'`, such as this:

            a = await zmq_ipc_pipe_end(ctx, 'a', endpoint, initialize=False)
            b = await zmq_ipc_pipe_end(ctx, 'b', endpoint)
            await a.initialize()

        In that case, prefer `zmq_ipc_pipe` for creating both ends.

        Side `'a'` will bind a `ROUTER` socket on the given endpoint;
        side `'b'` will connect a `DEALER` socket to the given endpoint.
        """

        if side == 'a':
            result = ZmqPipeEnd(ctx, zmq.ROUTER, endpoint, port=None, bind=True, serializer=serializer)
        elif side == 'b':
            result = ZmqPipeEnd(ctx, zmq.DEALER, endpoint, port=None, serializer=serializer)
        else:
            raise ValueError("side must be 'a' or 'b'")

        if initialize:
            await result.initialize()
        return result


    async def zmq_ipc_pipe(ctx, endpoint, *, serializer: Optional[Serializer]=None):
        a = await zmq_ipc_pipe_end(ctx, 'a', endpoint, serializer=serializer, initialize=False)
        b = await zmq_ipc_pipe_end(ctx, 'b', endpoint, serializer=serializer)
        await a.initialize()
        return a, b


    def zmq_inproc_pipe_end(ctx, side, endpoint=None, *, serializer: Optional[Serializer]=None):
        """
        Returns a `ZmqPipeEnd` backed by an `inproc` connection; the endpoint must contain the scheme part.
        The inproc transport uses `PAIR` sockets, not requiring `initialize()`.

        Side `'a'` will bind a `PAIR` socket on the given or a random endpoint;
        side `'b'` will connect a `PAIR` socket to the given endpoint.
        """

        if side == 'a':
            if endpoint is not None:
                return ZmqPipeEnd(ctx, zmq.PAIR, endpoint, port=None, bind=True, serializer=serializer)

            for i in range(100):
                endpoint = f'inproc://pipe-{random.randrange(2**32):#010x}'
                try:
                    return ZmqPipeEnd(ctx, zmq.PAIR, endpoint, port=None, bind=True)
                except zmq.ZMQError:  # pragma: nocover
                    pass
            else:  # pragma: nocover
                raise zmq.ZMQBindError("Could not bind socket to random pipe endpoint.")
        elif side == 'b':
            if endpoint is None:
                raise ValueError("b side requires endpoint argument")
            return ZmqPipeEnd(ctx, zmq.PAIR, endpoint, port=None, serializer=serializer)
        else:
            raise ValueError("side must be 'a' or 'b'")


    def zmq_inproc_pipe(ctx, endpoint=None, *, serializer: Optional[Serializer]=None):
        a = zmq_inproc_pipe_end(ctx, 'a', endpoint, serializer=serializer)
        b = zmq_inproc_pipe_end(ctx, 'b', a.endpoint, serializer=serializer)
        return a, b
