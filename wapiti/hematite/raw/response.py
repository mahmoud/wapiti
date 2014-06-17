# -*- coding: utf-8 -*-

from io import BytesIO

from hematite.raw import messages as M
from hematite.raw.parser import (StatusLine,
                                 HTTPVersion,
                                 HeadersWriter,
                                 ResponseReader,
                                 ResponseWriter,
                                 parse_message_traits)
from hematite.raw.messages import Complete
from hematite.raw.datastructures import Headers

DEFAULT_STATUS_CODE = 200
DEFAULT_REASON = 'OK'
DEFAULT_HTTP_VERSION = HTTPVersion(1, 1)

# Does None/None make more sense for defaults, allowing the
# instantiation of a truly blank RawResponse?


class RawResponse(object):
    def __init__(self, status_code=None, reason=None, headers=None, body=None,
                 http_version=None, **kwargs):
        status_line = kwargs.pop('status_line', None)
        if status_line:
            self.status_line = status_line
        else:
            self.status_code = status_code
            self.reason = reason
            self.http_version = http_version

        self.headers = headers or Headers()
        self.body = body

        traits = parse_message_traits(self.headers)
        self.chunked = kwargs.pop('chunked', traits.chunked)
        self.content_length = kwargs.pop('content_length',
                                         traits.content_length)
        self.connection_close = kwargs.pop('connection_close',
                                           traits.connection_close)
        if kwargs:
            raise TypeError('got unexpected kwargs: %r' % kwargs.keys())

    @property
    def status_line(self):
        return StatusLine(version=self.http_version,
                          status_code=self.status_code,
                          reason=self.reason)

    @status_line.setter
    def status_line(self, val):
        if isinstance(val, bytes):
            val = StatusLine.from_bytes(val)
        try:
            self.http_version, self.status_code, self.reason = val
        except:
            raise TypeError('expected StatusLine or tuple, not %r' % val)

    def get_writer(self):
        return ResponseWriter(status_line=self.status_line,
                              headers=HeadersWriter(self.headers),
                              body=[])  # TODO: bodies

    def to_bytes(self):
        writer = self.get_writer()
        return b''.join(part for _state, part in writer.writer if
                        _state != Complete.type)

    @classmethod
    def from_bytes(cls, bytestr):
        # TODO: generify
        bio = BytesIO(bytestr)
        reader = ResponseReader()
        state = reader.state
        while True:
            if state is M.Complete:
                break
            elif state.type == M.NeedLine.type:
                line = bio.readline()  # TODO: limit?
                next_state = M.HaveLine(value=line)
            elif state.type == M.NeedData.type:
                data = bio.read(state.amount)
                # TODO: can this block or return None if empty etc?
                next_state = M.HaveData(value=data)
            elif state.type == M.NeedPeek.type:
                peeked = bio.peek(state.amount)
                if not peeked:
                    pass  # TODO: again, what happens on end of stream
                next_state = M.HavePeek(amount=peeked)
            else:
                raise RuntimeError('Unknown state %r' % (state,))
            state = reader.send(next_state)

        return reader.raw_response

    def __repr__(self):
        cn = self.__class__.__name__
        parts = ['<%s "%s %s"' % (cn, self.status_code, self.reason)]
        if self.content_length:
            parts.append(' content_length=%s' % self.content_length)
        if self.chunked:
            parts.append(' +chunked')
        if self.connection_close:
            parts.append(' +connection_close')
        if self.headers:
            parts.append('\n  Headers:\n    ')
            _hlines = ['%s: %s' % hi for hi in self.headers.items(multi=True)]
            parts.append('\n    '.join(_hlines))
        if self.body:
            parts.append('\n  Body: %r' % self.body)
        parts.append(' >')
        return ''.join(parts)
