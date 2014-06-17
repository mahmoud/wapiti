# -*- coding: utf-8 -*-

import ssl
import time
import errno
import socket
from io import BlockingIOError

from hematite.async import join as async_join
from hematite.request import Request, RawRequest
from hematite.response import Response
from hematite.raw.parser import ResponseReader
from hematite.raw.drivers import SSLSocketDriver
from hematite.profile import HematiteProfile


class ConnectionError(Exception):  # TODO: maybe inherit from socket.error?
    def __init__(self, *a, **kw):
        self.socket_error = kw.pop('socket_error', None)
        super(ConnectionError, self).__init__(*a, **kw)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        cn = self.__class__.__name__
        if self.socket_error:
            return '%s(%r)' % (cn, self.socket_error)
        return super(ConnectionError, self).__repr__()


class UnknownHost(ConnectionError):
    pass


class UnreachableHost(ConnectionError):
    pass


class RequestTimeout(Exception):
    pass


DEFAULT_TIMEOUT = 10.0
CLIENT_METHODS = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                  'TRACE', 'OPTIONS', 'PATCH']  # CONNECT intentionally omitted


class ClientOperation(object):
    def __init__(self, client, method):
        self.client = client
        self.method = method

    def __call__(self, url, query_params=None, body=None,
                 timeout=DEFAULT_TIMEOUT):
        req = Request(self.method, url, body=body)
        if query_params:
            req._url.args.update(query_params)
        self.client.populate_headers(req)
        return self.client.request(request=req, timeout=timeout)

    def async(self, url, body=None):
        req = Request(self.method, url, body=body)
        self.client.populate_headers(req)
        return self.client.request(request=req, async=True)


class UnboundClientOperation(object):
    def __init__(self, method):
        self.method = method

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return ClientOperation(client=obj, method=self.method)

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(method=%r)' % (cn, self.method)


def lookup_url(url):
    host = url.host
    port = url.port or (443 if url.scheme.lower() == 'https' else 80)

    # here we use the value of url.family to indicate whether host
    # is already an IP or not. the user might have mucked with
    # this, so maybe a better check is in order.
    if url.family is None:
        # assuming TCP ;P
        # big wtf: no kwargs on getaddrinfo
        addrinfos = socket.getaddrinfo(host,
                                       port,
                                       socket.AF_UNSPEC,  # v4/v6
                                       socket.SOCK_STREAM,
                                       socket.IPPROTO_TCP)
        # TODO: configurable behavior on multiple returns?
        # TODO: (cont.) set preference for IPv4/v6

        # NOTE: raises exception on unresolvable hostname, so
        #       addrinfo[0] should never indexerror
        family, socktype, proto, canonname, sockaddr = addrinfos[0]
        ret = (family, socktype) + sockaddr
    elif url.family is socket.AF_INET:
        ret = (url.family, socket.SOCK_STREAM, host, port)
    elif url.family is socket.AF_INET6:
        # TODO: how to handle flowinfo, scopeid here? is None even valid?
        ret = (url.family, socket.SOCK_STREAM, host, port, None, None)
    else:
        raise ValueError('invalid family on url: %r' % url)

    # NOTE: it'd be cool to just return an unconnected socket
    # here, but even unconnected sockets use fds
    return ret


class Client(object):

    for client_method in CLIENT_METHODS:
        locals()[client_method.lower()] = UnboundClientOperation(client_method)
    del client_method

    def __init__(self, profile=None, user_agent=None):
        self.profile = profile or HematiteProfile()
        self.user_agent = user_agent

    def populate_headers(self, request):
        if self.profile:
            self.profile.populate_headers(request)
        if self.user_agent:
            request.user_agent = self.user_agent

    def get_addrinfo(self, request):
        # TODO: call from/merge with get_socket? would lose timing info
        # TODO: should one still run getaddrinfo even when a request has an IP
        # minor wtf: socket.getaddrinfo port can be a service name like 'http'
        url = request.host_url  # a URL object
        try:
            return lookup_url(url)
        except socket.error as se:
            raise UnknownHost(socket_error=se)

    # TODO: maybe split out addrinfo into relevant fields
    # TODO: make request optional?
    def get_socket(self, request, addrinfo, nonblocking):
        # yikes
        family, socktype, sockaddr = addrinfo[0], addrinfo[1], addrinfo[2:]

        ret = socket.socket(family, socktype)

        is_ssl = request.host_url.scheme.lower() == 'https'
        if nonblocking:
            ret.setblocking(0)
        if is_ssl:
            ret = ssl.wrap_socket(ret)

        try:
            conn_res = ret.connect_ex(sockaddr)
        except socket.error as se:
            conn_res = se.args[0]

        if conn_res:
            if conn_res not in (errno.EISCONN, errno.EWOULDBLOCK,
                                errno.EINPROGRESS, errno.EALREADY):
                socket.error('Unknown', conn_res)

        # djb points out that some socket error conditions are only
        # visible with this 'one weird old trick'
        err = ret.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            raise socket.error('Unknown', err)

        return ret

    def request(self,
                request,
                async=False,
                autoload_body=True,
                timeout=DEFAULT_TIMEOUT):
        # TODO: kwargs for raise_exc, follow_redirects
        kw = dict(client=self, request=request, autoload_body=autoload_body)
        client_resp = ClientResponse(**kw)
        if async:
            return client_resp
        async_join([client_resp], timeout=timeout)
        if not client_resp.is_complete:
            raise RequestTimeout('request did not complete within %s seconds'
                                 % timeout)
        return client_resp


class _OldState(object):
    # TODO: ssl_connect?

    (NotStarted, LookupHost, Connect, SendRequestHeaders, SendRequestBody,
     ReceiveResponseHeaders, ReceiveResponseBody, Complete) = range(8)

    # Alternate schemes:
    #
    # Past tense:
    # NotStarted, Started, HostResolved, Connected, RequestEnvelopeSent,
    # RequestSent, ResponseStarted, ResponseEnvelopeComplete, ResponseComplete
    #
    # Gerunds:
    # None, ResolvingHost, Connecting, SendingRequestEnvelope,
    # SendingRequestContent, Waiting, ReceivingResponse,
    # ReceivingResponseContent, Complete


class _State(object):
    # TODO: Securing/Handshaking
    # TODO: WaitingForContinue  # 100 Continue that is
    (NotStarted, ResolvingHost, Connecting, Sending, Receiving,
     Complete) = range(6)

"""RawRequest conversion paradigms:

if not isinstance(req, RawRequest):
    rreq = req.to_raw_request()

if isinstance(req, Request):
    rreq = RawRequest.from_request(req)

Which is more conducive to extensibility?

TODO: in order to enable sending a straight RawRequest, might need an
explicit URL field.
"""


class ClientResponse(object):
    def __init__(self, client, request=None, **kwargs):
        self.client = client
        self._set_request(request)

        self.state = _State.NotStarted
        self.socket = None
        self.driver = None
        self.timings = {'created': time.time()}
        # TODO: need to set error and Complete state on errors
        self.error = None

        self.raw_response = None

        self.autoload_body = kwargs.pop('autoload_body', True)
        self.nonblocking = kwargs.pop('nonblocking', False)
        self.timeout = kwargs.pop('timeout', None)
        self.follow_redirects = kwargs.pop('follow_redirects', None)
        if self.follow_redirects is True:
            self.follow_redirects = 3  # TODO: default limit?

        # TODO: request body/total bytes uploaded counters
        # TODO: response body/total bytes downloaded counters
        # (for calculating progress)

    def _set_request(self, request):
        self.request = request
        if request is None:
            self.raw_request = None  # TODO
        elif isinstance(request, RawRequest):
            self.raw_request = request
        elif isinstance(request, Request):
            self.raw_request = request.to_raw_request()
        else:
            raise TypeError('expected request to be a Request or RawRequest')

    def execute(self):
        while True:
            if self.want_write:
                self.do_write()
            elif self.want_read:
                self.do_read()
            else:
                break

    def fileno(self):
        if self.socket:
            return self.socket.fileno()
        return None  # or raise an exception?

    @property
    def norm_timings(self):
        t = self.timings
        return dict([(k, v - t['created']) for (k, v) in t.items()])

    @property
    def semantic_state(self):
        return ('TBI', 'TBI details')

    @property
    def is_complete(self):
        return self.state == _State.Complete

    @property
    def want_write(self):
        if self.error:
            return False
        driver = self.driver
        if not driver:
            return True  # to resolve hosts and connect
        return driver.want_write

    @property
    def want_read(self):
        if self.error:
            return False
        driver = self.driver
        if not driver:
            return False
        if driver.want_read:
            if not self.autoload_body and driver.inbound_headers_completed:
                return False
            return True
        return False

    def do_write(self):
        if self.error:
            return False
        if self.raw_request is None:
            raise ValueError('request not set')
        state, request = self.state, self.raw_request

        # TODO: BlockingIOErrors for DNS/connect?
        # TODO: SSLErrors on connect? (SSL is currently inside the driver)
        try:
            if state is _State.NotStarted:
                self.state += 1
                self.timings['started'] = time.time()
            elif state is _State.ResolvingHost:
                try:
                    self.addrinfo = self.client.get_addrinfo(request)
                except Exception as e:
                    self.error = e
                    raise
                else:
                    self.state += 1
                    self.timings['host_resolved'] = time.time()
            elif state is _State.Connecting:
                try:
                    self.socket = self.client.get_socket(request,
                                                         self.addrinfo,
                                                         self.nonblocking)
                    writer = self.raw_request.get_writer()
                    self.driver = SSLSocketDriver(self.socket,
                                                  reader=ResponseReader(),
                                                  writer=writer)
                except Exception as e:
                    self.error = e
                    raise
                else:
                    self.state += 1
                    self.timings['connected'] = time.time()
            elif state is _State.Sending:
                try:
                    if self.driver.write():
                        self.state += 1
                        self.timings['sent'] = time.time()
                except Exception as e:
                    self.error = e
                    raise
            else:
                raise RuntimeError('not in a writable state: %r' % state)
        except BlockingIOError:
            return False
        return self.want_write

    def get_data(self):
        return self.driver.reader.raw_response.body.data

    @property
    def url(self):
        return self.raw_request.url

    def do_read(self):
        if self.error:
            return False
        state = self.state
        try:
            if state is _State.Receiving:
                self.raw_response = self.driver.reader.raw_response
                self.timings['first_read'] = time.time()
                try:
                    res = self.driver.read()
                    if res:
                        self.state += 1
                        self.timings['complete'] = time.time()
                        resp = Response.from_raw_response(self.raw_response)
                        self.response = resp
                except Exception as e:
                    self.error = e
                    raise
            else:
                raise RuntimeError('not in a readable state: %r' % state)
        except BlockingIOError:
            return False
        return self.want_read
        # TODO: return socket
        # TODO: how to resolve socket returns with as-yet-unfetched body
        # (terminology: lazily-fetched?)
        # TODO: compression support goes where? how about charset decoding?
        # TODO: callback on read complete (to release socket)
