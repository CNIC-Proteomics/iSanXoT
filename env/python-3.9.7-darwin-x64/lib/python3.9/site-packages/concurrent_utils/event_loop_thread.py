import asyncio
from contextlib import contextmanager
import sys
import threading


class EventLoopThread(object):
    """\
    A dedicated thread running an event loop.
    Synchronous methods are provided to run code on that event loop.
    Coroutines, callbacks and asynchronous context managers can be used from non-async code this way.

    Take care to start the event loop thread before using it::

        thread = EventLoopThread()
        # thread.call_soon(print, "foo")  # bad: thread is not running
        with thread:
            thread.call_soon(print, "foo")  # good: thread is running
    """

    def __init__(self):
        self.loop = None  # type: asyncio.AbstractEventLoop
        self._condition = threading.Condition()

    def _create_loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.new_event_loop()

    def _run(self):
        with self._condition:
            self.loop = self._create_loop()
            asyncio.set_event_loop(self.loop)
            self._condition.notify()
        try:
            self.loop.run_forever()
        finally:
            with self._condition:
                asyncio.set_event_loop(None)
                self.loop.close()
                self.loop = None
                self._condition.notify()

    def __enter__(self):
        """\
        Starts a dedicated thread for running the event loop.
        Blocks until the loop is running.
        """
        with self._condition:
            threading.Thread(target=self._run).start()
            self._condition.wait_for(lambda: self.loop is not None)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """\
        Stops the thread running the event loop.
        Blocks until the loop is stopped completely.
        """
        with self._condition:
            self.call_soon(self.loop.stop)
            self._condition.wait_for(lambda: self.loop is None)

    def call_soon(self, callback, *args):
        """\
        Schedules the given callback on the event loop.
        See `AbstractEventLoop.call_soon_threadsafe`.
        """
        return self.loop.call_soon_threadsafe(callback, *args)

    def run_coroutine(self, coro):
        """\
        Runs the given coroutine on the event loop.
        See `asyncio.run_coroutine_threadsafe`.
        """
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    @contextmanager
    def context(self, async_context):
        """\
        Opens the given asynchronous contest manager on the event loop.
        For a context manager that would be called like this::

            async with ctx as value:
                body

        This method allows a call like this::

            with event_loop_thread.context(ctx) as value:
                body

        The asynchronous work of the context manager is run on the dedicated thread.
        """

        exit = type(async_context).__aexit__
        value = self.run_coroutine(type(async_context).__aenter__(async_context)).result()
        exc = True
        try:
            try:
                yield value
            except:
                exc = False
                if not self.run_coroutine(exit(async_context, *sys.exc_info())).result():
                    raise
        finally:
            if exc:
                self.run_coroutine(exit(async_context, None, None, None)).result()
