# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

"""
A specialized IO loop on top of asyncore adding support for epoll()
on Linux and kqueue() and OSX/BSD, dramatically increasing performances
offered by base asyncore module.

poll() and select() loops are also reimplemented and are an order of
magnitude faster as they support fd un/registration and modification.

This module is not supposed to be used directly unless you want to
include a new dispatcher which runs within the main FTP server loop,
in which case:
  __________________________________________________________________
 |                      |                                           |
 | INSTEAD OF           | ...USE:                                   |
 |______________________|___________________________________________|
 |                      |                                           |
 | asyncore.dispacher   | Acceptor (for servers)                    |
 | asyncore.dispacher   | Connector (for clients)                   |
 | asynchat.async_chat  | AsyncChat (for a full duplex connection ) |
 | asyncore.loop        | FTPServer.server_forever()                |
 |______________________|___________________________________________|

asyncore.dispatcher_with_send is not supported, same for "map" argument
for asyncore.loop and asyncore.dispatcher and asynchat.async_chat
constructors.

Follows a server example:

import socket
from pyftpdlib.ioloop import IOLoop, Acceptor, AsyncChat

class Handler(AsyncChat):

    def __init__(self, sock):
        AsyncChat.__init__(self, sock)
        self.push('200 hello\r\n')
        self.close_when_done()

class Server(Acceptor):

    def __init__(self, host, port):
        Acceptor.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        Handler(sock)

server = Server('localhost', 8021)
IOLoop.instance().loop()
"""

import asyncio
import errno
import heapq
import os
import select
import socket
import sys
import time
import traceback
try:
    import threading
except ImportError:
    import dummy_threading as threading

from ._compat import callable
from .log import config_logging
from .log import debug
from .log import is_logging_configured
from .log import logger


timer = getattr(time, 'monotonic', time.time)

# These errnos indicate that a connection has been abruptly terminated.
_ERRNOS_DISCONNECTED = set((
    errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN, errno.ECONNABORTED,
    errno.EPIPE, errno.EBADF, errno.ETIMEDOUT))
if hasattr(errno, "WSAECONNRESET"):
    _ERRNOS_DISCONNECTED.add(errno.WSAECONNRESET)
if hasattr(errno, "WSAECONNABORTED"):
    _ERRNOS_DISCONNECTED.add(errno.WSAECONNABORTED)

# These errnos indicate that a non-blocking operation must be retried
# at a later time.
_ERRNOS_RETRY = set((errno.EAGAIN, errno.EWOULDBLOCK))
if hasattr(errno, "WSAEWOULDBLOCK"):
    _ERRNOS_RETRY.add(errno.WSAEWOULDBLOCK)


class RetryError(Exception):
    pass


# ===================================================================
# --- scheduler
# ===================================================================

class _Scheduler(object):
    """Run the scheduled functions due to expire soonest (if any)."""

    def __init__(self):
        # the heap used for the scheduled tasks
        self._tasks = []
        self._cancellations = 0

    def poll(self):
        """Run the scheduled functions due to expire soonest and
        return the timeout of the next one (if any, else None).
        """
        now = timer()
        calls = []
        while self._tasks:
            if now < self._tasks[0].timeout:
                break
            call = heapq.heappop(self._tasks)
            if call.cancelled:
                self._cancellations -= 1
            else:
                calls.append(call)

        for call in calls:
            if call._repush:
                heapq.heappush(self._tasks, call)
                call._repush = False
                continue
            try:
                call.call()
            except Exception:
                logger.error(traceback.format_exc())

        # remove cancelled tasks and re-heapify the queue if the
        # number of cancelled tasks is more than the half of the
        # entire queue
        if (self._cancellations > 512 and
                self._cancellations > (len(self._tasks) >> 1)):
            debug("re-heapifying %s cancelled tasks" % self._cancellations)
            self.reheapify()

        try:
            return max(0, self._tasks[0].timeout - now)
        except IndexError:
            pass

    def register(self, what):
        """Register a _CallLater instance."""
        heapq.heappush(self._tasks, what)

    def unregister(self, what):
        """Unregister a _CallLater instance.
        The actual unregistration will happen at a later time though.
        """
        self._cancellations += 1

    def reheapify(self):
        """Get rid of cancelled calls and reinitialize the internal heap."""
        self._cancellations = 0
        self._tasks = [x for x in self._tasks if not x.cancelled]
        heapq.heapify(self._tasks)


class _CallLater(object):
    """Container object which instance is returned by ioloop.call_later()."""

    __slots__ = ('_delay', '_target', '_args', '_kwargs', '_errback', '_sched',
                 '_repush', 'timeout', 'cancelled')

    def __init__(self, seconds, target, *args, **kwargs):
        assert callable(target), "%s is not callable" % target
        assert sys.maxsize >= seconds >= 0, \
            "%s is not greater than or equal to 0 seconds" % seconds
        self._delay = seconds
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._errback = kwargs.pop('_errback', None)
        self._sched = kwargs.pop('_scheduler')
        self._repush = False
        # seconds from the epoch at which to call the function
        if not seconds:
            self.timeout = 0
        else:
            self.timeout = timer() + self._delay
        self.cancelled = False
        self._sched.register(self)

    def __lt__(self, other):
        return self.timeout < other.timeout

    def __le__(self, other):
        return self.timeout <= other.timeout

    def __repr__(self):
        if self._target is None:
            sig = object.__repr__(self)
        else:
            sig = repr(self._target)
        sig += ' args=%s, kwargs=%s, cancelled=%s, secs=%s' % (
            self._args or '[]', self._kwargs or '{}', self.cancelled,
            self._delay)
        return '<%s>' % sig

    __str__ = __repr__

    def _post_call(self, exc):
        if not self.cancelled:
            self.cancel()

    def call(self):
        """Call this scheduled function."""
        assert not self.cancelled, "already cancelled"
        exc = None
        try:
            self._target(*self._args, **self._kwargs)
        except Exception as _:
            exc = _
            if self._errback is not None:
                self._errback()
            else:
                raise
        finally:
            self._post_call(exc)

    def reset(self):
        """Reschedule this call resetting the current countdown."""
        assert not self.cancelled, "already cancelled"
        self.timeout = timer() + self._delay
        self._repush = True

    def cancel(self):
        """Unschedule this call."""
        if not self.cancelled:
            self.cancelled = True
            self._target = self._args = self._kwargs = self._errback = None
            self._sched.unregister(self)


class _CallEvery(_CallLater):
    """Container object which instance is returned by IOLoop.call_every()."""

    __slots__ = ('_delay', '_target', '_args', '_kwargs', '_errback', '_sched',
                 '_repush', 'timeout', 'cancelled')

    def __init__(self, seconds, target, *args, **kwargs):
        assert callable(target), "%s is not callable" % target
        assert sys.maxsize >= seconds >= 0, \
            "%s is not greater than or equal to 0 seconds" % seconds
        self._delay = seconds
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._errback = kwargs.pop('_errback', None)
        self._sched = kwargs.pop('_scheduler')
        self._repush = False
        # seconds from the epoch at which to call the function
        if not seconds:
            self.timeout = 0
        else:
            self.timeout = timer() + self._delay
        self.cancelled = False
        self._sched.register(self)

    def _post_call(self, exc):
        if not self.cancelled:
            self.timeout = timer() + self._delay
            self._repush = True


class _IOLoop(object):
    """Base class which will later be referred as IOLoop."""

    READ = 1
    WRITE = 2
    _instance = None
    _lock = threading.Lock()
    _started_once = False

    def __init__(self):
        self.socket_map = {}
        self.sched = _Scheduler()
        self.loop = asyncio.get_event_loop()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self):
        status = [self.__class__.__module__ + "." + self.__class__.__name__]
        status.append("(fds=%s, tasks=%s)" % (
            len(self.socket_map), len(self.sched._tasks)))
        return '<%s at %#x>' % (' '.join(status), id(self))

    __str__ = __repr__

    @classmethod
    def instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, fd, instance, events):
        self.socket_map[fd] = instance

    def unregister(self, fd):
        if fd in self.socket_map:
            del self.socket_map[fd]

    def modify(self, fd, events):
        pass

    def poll(self, timeout):
        self.loop.run_until_complete(asyncio.sleep(timeout))

    def loop(self, timeout=None, blocking=True):
        if not self._started_once:
            self._started_once = True
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    def call_later(self, seconds, target, *args, **kwargs):
        return self.loop.call_later(seconds, target, *args, **kwargs)

    def call_every(self, seconds, target, *args, **kwargs):
        return self.loop.call_every(seconds, target, *args, **kwargs)

    def close(self):
        self.loop.close()


# ===================================================================
# --- select() - POSIX / Windows
# ===================================================================

class Select(_IOLoop):
    """select() based poller."""

    def __init__(self):
        _IOLoop.__init__(self)

    def register(self, fd, instance, events):
        self.socket_map[fd] = instance

    def unregister(self, fd):
        if fd in self.socket_map:
            del self.socket_map[fd]

    def modify(self, fd, events):
        pass

    def poll(self, timeout):
        self.loop.run_until_complete(asyncio.sleep(timeout))


# ===================================================================
# --- poll() / epoll()
# ===================================================================

class _BasePollEpoll(_IOLoop):
    """Base class for poll() and epoll() based pollers."""

    def __init__(self):
        _IOLoop.__init__(self)

    def register(self, fd, instance, events):
        self.socket_map[fd] = instance

    def unregister(self, fd):
        if fd in self.socket_map:
            del self.socket_map[fd]

    def modify(self, fd, events):
        pass

    def poll(self, timeout):
        self.loop.run_until_complete(asyncio.sleep(timeout))


# ===================================================================
# --- poll() - POSIX
# ===================================================================

if hasattr(select, 'poll'):

    class Poll(_BasePollEpoll):
        """poll() based poller."""

        READ = select.POLLIN
        WRITE = select.POLLOUT
        _ERROR = select.POLLERR | select.POLLHUP | select.POLLNVAL
        _poller = select.poll

        def __init__(self):
            _BasePollEpoll.__init__(self)

        def modify(self, fd, events):
            pass

        def poll(self, timeout):
            self.loop.run_until_complete(asyncio.sleep(timeout))


# ===================================================================
# --- /dev/poll - Solaris (introduced in python 3.3)
# ===================================================================

if hasattr(select, 'devpoll'):  # pragma: no cover

    class DevPoll(_BasePollEpoll):
        """/dev/poll based poller (introduced in python 3.3)."""

        READ = select.POLLIN
        WRITE = select.POLLOUT
        _ERROR = select.POLLERR | select.POLLHUP | select.POLLNVAL
        _poller = select.devpoll

        def __init__(self):
            _BasePollEpoll.__init__(self)

        def fileno(self):
            return self._poller.fileno()

        def modify(self, fd, events):
            pass

        def poll(self, timeout):
            self.loop.run_until_complete(asyncio.sleep(timeout))

        def close(self):
            self.loop.close()


# ===================================================================
# --- epoll() - Linux
# ===================================================================

if hasattr(select, 'epoll'):

    class Epoll(_BasePollEpoll):
        """epoll() based poller."""

        READ = select.EPOLLIN
        WRITE = select.EPOLLOUT
        _ERROR = select.EPOLLERR | select.EPOLLHUP
        _poller = select.epoll

        def __init__(self):
            _BasePollEpoll.__init__(self)

        def fileno(self):
            return self._poller.fileno()

        def close(self):
            self.loop.close()


# ===================================================================
# --- kqueue() - BSD / OSX
# ===================================================================

if hasattr(select, 'kqueue'):  # pragma: no cover

    class Kqueue(_IOLoop):
        """kqueue() based poller."""

        def __init__(self):
            _IOLoop.__init__(self)
            self._kqueue = select.kqueue()
            self._active = {}

        def fileno(self):
            """Return kqueue() fd."""
            return self._kqueue.fileno()

        def close(self):
            _IOLoop.close(self)
            self._kqueue.close()

        def register(self, fd, instance, events):
            self.socket_map[fd] = instance
            try:
                self._control(fd, events, select.KQ_EV_ADD)
            except EnvironmentError as err:
                if err.errno == errno.EEXIST:
                    debug("call: register(); poller raised EEXIST; ignored",
                          self)
                else:
                    raise
            self._active[fd] = events

        def unregister(self, fd):
            try:
                del self.socket_map[fd]
                events = self._active.pop(fd)
            except KeyError:
                pass
            else:
                try:
                    self._control(fd, events, select.KQ_EV_DELETE)
                except EnvironmentError as err:
                    if err.errno in (errno.ENOENT, errno.EBADF):
                        debug("call: unregister(); poller returned %r; "
                              "ignoring it" % err, self)
                    else:
                        raise

        def modify(self, fd, events):
            instance = self.socket_map[fd]
            self.unregister(fd)
            self.register(fd, instance, events)

        def _control(self, fd, events, flags):
            kevents = []
            if events & self.WRITE:
                kevents.append(select.kevent(
                    fd, filter=select.KQ_FILTER_WRITE, flags=flags))
            if events & self.READ or not kevents:
                # always read when there is not a write
                kevents.append(select.kevent(
                    fd, filter=select.KQ_FILTER_READ, flags=flags))
            # even though control() takes a list, it seems to return
            # EINVAL on Mac OS X (10.6) when there is more than one
            # event in the list
            for kevent in kevents:
                self._kqueue.control([kevent], 0)

        # localize variable access to minimize overhead
        def poll(self,
                 timeout,
                 _len=len,
                 _READ=select.KQ_FILTER_READ,
                 _WRITE=select.KQ_FILTER_WRITE,
                 _EOF=select.KQ_EV_EOF,
                 _ERROR=select.KQ_EV_ERROR):
            try:
                kevents = self._kqueue.control(None, _len(self.socket_map),
                                               timeout)
            except OSError as err:
                if err.errno == errno.EINTR:
                    return
                raise
            for kevent in kevents:
                inst = self.socket_map.get(kevent.ident)
                if inst is None:
                    continue
                if kevent.filter == _READ:
                    if inst.readable():
                        _read(inst)
                if kevent.filter == _WRITE:
                    if kevent.flags & _EOF:
                        # If an asynchronous connection is refused,
                        # kqueue returns a write event with the EOF
                        # flag set.
                        # Note that for read events, EOF may be returned
                        # before all data has been consumed from the
                        # socket buffer, so we only check for EOF on
                        # write events.
                        inst.handle_close()
                    else:
                        if inst.writable():
                            _write(inst)
                if kevent.flags & _ERROR:
                    inst.handle_close()


# ===================================================================
# --- choose the better poller for this platform
# ===================================================================

if hasattr(select, 'epoll'):      # epoll() - Linux
    IOLoop = Epoll
elif hasattr(select, 'kqueue'):   # kqueue() - BSD / OSX
    IOLoop = Kqueue
elif hasattr(select, 'devpoll'):  # /dev/poll - Solaris
    IOLoop = DevPoll
elif hasattr(select, 'poll'):     # poll() - POSIX
    IOLoop = Poll
else:                             # select() - POSIX and Windows
    IOLoop = Select


# ===================================================================
# --- asyncore dispatchers
# ===================================================================

# these are overridden in order to register() and unregister()
# file descriptors against the new pollers


class AsyncChat(asyncio.Protocol):
    """A class for handling asynchronous communication."""

    def __init__(self, sock=None, ioloop=None):
        self.sock = sock
        self.ioloop = ioloop
        self.transport = None
        self.protocol = None
        self._buffer = []
        self._buffer_len = 0
        self._terminator = b"\r\n"
        self._wanted_io_events = 0
        self._initialized = False
        self._closing = False
        self._closed = False
        self.connected = True  # 兼容 asynchat/asyncore 旧逻辑
        self._lastdata = 0
        self._had_cr = False
        self._start_time = timer()
        self._resp = ()
        self._offset = None
        self._filefd = None
        self._idler = None
        self._initialized = False
        try:
            if sock is not None:
                self.transport, self.protocol = self.ioloop.create_connection(
                    lambda: self, sock=sock)
        except socket.error as err:
            # if we get an exception here we want the dispatcher
            # instance to set socket attribute before closing, see:
            # https://github.com/giampaolo/pyftpdlib/issues/188
            self.transport, self.protocol = self.ioloop.create_connection(
                lambda: self, sock=socket.socket())
            # https://github.com/giampaolo/pyftpdlib/issues/143
            self.close()
            if err.errno == errno.EINVAL:
                return
            self.handle_error()
            return

        # remove this instance from IOLoop's socket map
        if not self.connected:
            self.close()
            return
        if self.timeout:
            self._idler = self.ioloop.call_every(self.timeout,
                                                 self.handle_timeout,
                                                 _errback=self.handle_error)

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self._buffer.append(data)
        self._buffer_len += len(data)
        # Flush buffer if it gets too long (possible DoS attacks).
        # RFC-959 specifies that a 500 response could be given in
        # such cases
        buflimit = 2048
        if self._buffer_len > buflimit:
            self.respond_w_warning('500 Command too long.')
            self._buffer = []
            self._buffer_len = 0

    def connection_lost(self, exc):
        self.handle_close()

    def push(self, data):
        self._initialized = True
        self.modify_ioloop_events(self.ioloop.WRITE)
        self._wanted_io_events = self.ioloop.WRITE
        self.transport.write(data)

    def push_with_producer(self, producer):
        self._initialized = True
        self.modify_ioloop_events(self.ioloop.WRITE)
        self._wanted_io_events = self.ioloop.WRITE
        if self.use_sendfile():
            self._offset = producer.file.tell()
            self._filefd = self.file_obj.fileno()
            try:
                self.initiate_sendfile()
            except _GiveUpOnSendfile:
                pass
            else:
                self.initiate_send = self.initiate_sendfile
                return
        debug("starting transfer using send()", self)
        self.push(producer.more())

    def close_when_done(self):
        self._closing = True

    def initiate_send(self):
        if self._buffer:
            self.transport.write(b''.join(self._buffer))
            self._buffer = []
            self._buffer_len = 0

    def initiate_sendfile(self):
        """A wrapper around sendfile."""
        try:
            sent = sendfile(self.transport.get_extra_info('socket').fileno(), self._filefd, self._offset,
                            self.ac_out_buffer_size)
        except OSError as err:
            if err.errno in _ERRNOS_RETRY or err.errno == errno.EBUSY:
                return
            elif err.errno in _ERRNOS_DISCONNECTED:
                self.handle_close()
            else:
                if self.tot_bytes_sent == 0:
                    logger.warning(
                        "sendfile() failed; falling back on using plain send")
                    raise _GiveUpOnSendfile
                else:
                    raise
        else:
            if sent == 0:
                # this signals the channel that the transfer is completed
                self.discard_buffers()
                self.handle_close()
            else:
                self._offset += sent
                self.tot_bytes_sent += sent

    def close(self):
        """Close the current channel disconnecting the client."""
        debug("call: close()", inst=self)
        if not self._closed:
            self._closed = True
            if self.transport is not None:
                self.transport.close()

            self._shutdown_connecting_dtp()

            if self.data_channel is not None:
                self.data_channel.close()
                del self.data_channel

            if self._out_dtp_queue is not None:
                file = self._out_dtp_queue[2]
                if file is not None:
                    file.close()
            if self._in_dtp_queue is not None:
                file = self._in_dtp_queue[0]
                if file is not None:
                    file.close()

            del self._out_dtp_queue
            del self._in_dtp_queue

            if self._idler is not None and not self._idler.cancelled:
                self._idler.cancel()

            # remove client IP address from ip map
            if self.remote_ip in self.server.ip_map:
                self.server.ip_map.remove(self.remote_ip)

            if self.fs is not None:
                self.fs.cmd_channel = None
                self.fs = None
            self.log("FTP session closed (disconnect).")
            # Having self.remote_ip not set means that no connection
            # actually took place, hence we're not interested in
            # invoking the callback.
            if self.remote_ip:
                self.ioloop.call_later(0, self.on_disconnect,
                                       _errback=self.handle_error)


class Connector(AsyncChat):
    """A class for handling asynchronous connections."""

    def add_channel(self, map=None, events=None):
        pass


class Acceptor(AsyncChat):
    """A class for handling asynchronous acceptors."""

    def add_channel(self, map=None, events=None):
        pass

    def bind_af_unspecified(self, addr):
        """Same as bind() but guesses address family from addr.
        Return the address family just determined.
        """
        assert self.socket is None
        host, port = addr
        err = "getaddrinfo() returned an empty list"
        info = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                   socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
        for res in info:
            self.socket = None
            af, socktype, proto, canonname, sa = res
            try:
                self.create_socket(af, socktype)
                self.bind(sa)
            except socket.error as _:
                err = _
                if self.socket is not None:
                    self.socket.close()
                    self.del_channel()
                    self.socket = None
                continue
            break
        if self.socket is None:
            self.del_channel()
            raise socket.error(err)
        return af

    def listen(self, num):
        self.socket.listen(num)

    def handle_accept(self):
        try:
            sock, addr = self.socket.accept()
        except socket.error as err:
            if err.errno in _ERRNOS_RETRY:
                return
            raise
        self.handle_accepted(sock, addr)

    def handle_accepted(self, sock, addr):
        """Called when a new connection is accepted."""
        pass

    def set_reuse_addr(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
