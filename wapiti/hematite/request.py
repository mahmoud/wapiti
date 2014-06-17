# -*- coding: utf-8 -*-

from collections import Iterable
from hematite.raw import RawRequest, Headers
from hematite.raw.parser import HTTPVersion


from hematite import serdes
from hematite.url import parse_hostinfo
from hematite.fields import REQUEST_FIELDS, HTTP_REQUEST_FIELDS
from hematite.raw.datastructures import Body, ChunkedBody

DEFAULT_METHOD = 'GET'
DEFAULT_VERSION = HTTPVersion(1, 1)
DEFAULT_SCHEME = 'http'


class Request(object):
    def __init__(self, method=None, url=None, **kw):
        self.method = method or DEFAULT_METHOD
        self.http_version = kw.pop('http_version', DEFAULT_VERSION)

        self._raw_url = url or None
        self._raw_headers = kw.pop('headers', Headers())

        self.url = self._raw_url
        self._init_headers()

        # TODO: maybe should defer this
        _url = self._url
        host_header = self.headers.get('Host')
        if not _url.host and host_header:
            if host_header:
                family, host, port = parse_hostinfo(host_header)
                _url.family, _url.host, _url.port = family, host, port
        if not host_header and _url.host:
            self.host = _url.http_request_host
        if not _url.scheme:
            _url.scheme = DEFAULT_SCHEME

        body = kw.pop('body', None)
        self.set_body(body)

    def set_body(self, value):
        self._body = None
        self.content_length = None
        self.chunked = False

        if isinstance(value, str):
            self._body = Body(value)
            self.content_length = len(value)
        elif not value:
            self._body = None
        elif isinstance(value, Iterable):
            self._body = ChunkedBody(value)
            self.chunked = True
        else:
            raise ValueError('Body must be string, iterable of strings '
                             'or None')

    # TODO: could use a metaclass for this, could also build it at init
    _header_field_map = dict([(hf.http_name, hf)
                              for hf in HTTP_REQUEST_FIELDS])
    locals().update([(hf.attr_name, hf) for hf in REQUEST_FIELDS])
    _init_headers = serdes._init_headers
    _get_header_dict = serdes._get_headers

    def get_copy(self):
        type_self = type(self)
        # to account for changing init signatures:
        ret = type_self.__new__(type_self)
        # covers basic immutable attrs (method, version), and
        # unanticipated attributes
        ret.__dict__.update(self.__dict__)
        # now, to override/actually set a few critical fields
        # TODO: make a copy of raw headers, too?
        ret.headers = Headers()
        for header, value in self.headers.items():  # TODO multi=True?
            _get_hv_copy = getattr(value, 'get_copy', None)
            if callable(_get_hv_copy):
                ret.headers[header] = _get_hv_copy()
            else:
                ret.headers[header] = value
        #ret._url = self._url.get_copy()
        # TODO ret.cookies = self.cookies

    @classmethod
    def from_raw_request(cls, raw_req):
        kw = {'method': raw_req.method,
              'url': raw_req.url,
              'version': raw_req.http_version,
              'headers': raw_req.headers,
              'body': raw_req.body}
        return cls(**kw)

    def to_raw_request(self):
        url = self._url.http_request_url
        headers = self._get_header_dict()
        if self.content_length is not None:
            headers['Content-Length'] = self.content_length
        elif self.chunked:
            headers['Transfer-Encoding'] = 'chunked'
        return RawRequest(method=self.method,
                          url=url,
                          host_url=self._url,
                          http_version=self.http_version,
                          headers=headers,
                          body=self._body)

    @classmethod
    def from_bytes(cls, bytestr):
        rr = RawRequest.from_bytes(bytestr)
        return cls.from_raw_request(rr)

    def to_bytes(self):
        raw_req = self.to_raw_request()
        return raw_req.to_bytes()

    def validate(self):
        pass
