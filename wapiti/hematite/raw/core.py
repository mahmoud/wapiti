import os
import errno
from io import BlockingIOError
import re

# TODO: make configurable
MAXLINE = 2 ** 19


def _cut(s, to=MAXLINE):
    if len(s) <= to:
        return s
    return s[:to]


# RFC 2616 p.17
_CRLF = '\r\n'
_LWS = _CRLF + ' \t'
_LINEAR_WS = ' \t\v\f'
START_LINE_SEP = re.compile('[' + _LINEAR_WS + ']+')

# <any US-ASCII control character (octets 0 - 31) and DEL (127)>
_CTL = ''.join(chr(i) for i in xrange(0, 32)) + chr(127)

_SEPARATORS = r'()<>@,;:\"/[]?={} ' + '\t'
_TOKEN_EXCLUDE = ''.join(set(_CTL) | set(_SEPARATORS))
TOKEN = re.compile('[^' + re.escape(_TOKEN_EXCLUDE) + ']+')

# <any OCTET except CTLs, but including LWS>
_TEXT_EXCLUDE = ''.join(set(_CTL) - set(_LWS))
TEXT = re.compile('[^' + _TEXT_EXCLUDE + ']+')

# this *should* be CRLF but not everything uses that as its delineator
# TODO: do we have to be able to recognize just carriage returns?
_LINE_END = '(?:(?:\r\n)|\n)'
LINE_END = re.compile(_LINE_END, re.DOTALL)
HEADERS_END = re.compile((_LINE_END * 2), re.DOTALL)


class HTTPException(Exception):
    def __init__(self, msg=None, raw=None):
        if raw:
            try:
                msg = ''.join([msg or '<unknown>', ': ', _cut(raw)])
            except:
                pass
        super(HTTPException, self).__init__(msg)


class ReadException(HTTPException):
    pass


class OverlongRead(ReadException):
    pass


class IncompleteRead(ReadException):
    pass


class EndOfStream(ReadException):
    pass


def readline(io_obj):
    line = io_obj.readline(MAXLINE)
    if not line:
        raise EndOfStream
    elif len(line) == MAXLINE and not LINE_END.match(line):
        raise OverlongRead
    return line


def eagain(characters_written=0):
    # TODO: no os.strerror on windows
    err = BlockingIOError(errno.EAGAIN,
                          os.strerror(errno.EAGAIN))
    err.characters_written = characters_written
    return err
