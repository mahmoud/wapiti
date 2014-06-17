import pytest

from hematite.url import URL
from hematite.raw import parser as P
from hematite.raw import datastructures as D
from hematite.raw import messages as M
from itertools import izip


@pytest.mark.parametrize('input,expected',
                         [('HTTP/0.9', P.HTTPVersion(0, 9)),
                          ('HTTP/1.0', P.HTTPVersion(1, 0)),
                          ('HTTP/1.1', P.HTTPVersion(1, 1)),
                          ('HTTP/2.0', P.HTTPVersion(2, 0))])
def test_HTTPVersion_froms(input, expected):
    """HTTPVersion.from_* should parse valid HTTP versions."""

    assert P.HTTPVersion.from_bytes(input) == expected
    m = P.HTTPVersion.PARSE_VERSION.match(input)
    assert P.HTTPVersion.from_match(m) == expected


@pytest.mark.parametrize('input,expected',
                         [('HTTP1/.a', P.InvalidVersion),
                          ('SDF1/1', P.InvalidVersion)])
def test_HTTPVersion_froms_raises(input, expected):
    """HTTPVersion.from_* should fail to parse invalid HTTP versions."""

    with pytest.raises(expected):
        P.HTTPVersion.from_bytes(input)

    with pytest.raises(expected):
        m = P.HTTPVersion.PARSE_VERSION.match(input)
        P.HTTPVersion.from_match(m)


@pytest.mark.parametrize('input,expected',
                         [(P.HTTPVersion(major=0, minor=9), 'HTTP/0.9'),
                          (P.HTTPVersion(major=1, minor=0), 'HTTP/1.0'),
                          (P.HTTPVersion(major=1, minor=1), 'HTTP/1.1'),
                          (P.HTTPVersion(major=2, minor=0), 'HTTP/2.0')])
def test_HTTPVersion_to_bytes(input, expected):
    """HTTPVersion.to_bytes should generate a valid HTTP Version."""

    assert bytes(input) == expected
    assert input.to_bytes() == expected


def test_HTTPVersion_round_trip():
    """HTTPVersion.from_* should parse the output of HTTPVersion.to_bytes"""

    expected = P.HTTPVersion(1, 1)
    assert P.HTTPVersion.from_bytes(expected.to_bytes()) == expected


@pytest.mark.parametrize(
    'input,expected',
    [('HTTP/1.1 200 OK\n',
      P.StatusLine(P.HTTPVersion(1, 1), 200, 'OK')),

     ('HTTP/1.1 200 OK\r\n',
      P.StatusLine(P.HTTPVersion(1, 1), 200, 'OK')),

     ('HTTP/1.0 404 Not Found\r\n',
      P.StatusLine(P.HTTPVersion(1, 0), 404, 'Not Found')),

     ('HTTP/1.1 500\r\n',
      P.StatusLine(P.HTTPVersion(1, 1), 500, 'Internal Server Error')),

     ('HTTP/1.1 500 Something went wrong\r\n',
      P.StatusLine(P.HTTPVersion(1, 1), 500, 'Something went wrong'))])
def test_StatusLine_froms(input, expected):
    """StatusLine.from_* should parse valid Status Lines, with or without
    reasons."""
    assert P.StatusLine.from_bytes(input) == expected
    m = P.StatusLine.PARSE_STATUS_LINE.match(input)
    assert P.StatusLine.from_match(m) == expected


@pytest.mark.parametrize(
    'input,expected',
    [('HTTP/1.1  OK\r\n', P.InvalidStatusCode),

     ('HTTP/Wrong 200 OK\r\n', P.InvalidVersion),

     ('Completely unparseable\r\n', P.InvalidStatusLine)])
def test_StatusLine_froms_raises(input, expected):
    """StatusLine.from_* should fail to parse invalid status lines."""
    with pytest.raises(expected):
        P.StatusLine.from_bytes(input)

    with pytest.raises(expected):
        P.StatusLine.from_match(P.StatusLine.PARSE_STATUS_LINE.match(input))


@pytest.mark.parametrize(
    'input,expected',
    [(P.StatusLine(version=P.HTTPVersion(major=1, minor=1),
                   status_code=200,
                   reason='OK'),
      'HTTP/1.1 200 OK'),

     (P.StatusLine(version=P.HTTPVersion(major=1, minor=0),
                   status_code=404,
                   reason='Not Found'),
      'HTTP/1.0 404 Not Found'),

     (P.StatusLine(version=P.HTTPVersion(major=1, minor=1),
                   status_code=500,
                   reason=''),
      'HTTP/1.1 500'),

     (P.StatusLine(version=P.HTTPVersion(major=1, minor=1),
                   status_code=500,
                   reason=None),
      'HTTP/1.1 500 Internal Server Error'),

     (P.StatusLine(version=P.HTTPVersion(major=1, minor=1),
                   status_code=500,
                   reason='Something went wrong'),
      'HTTP/1.1 500 Something went wrong')])
def test_StatusLine_to_bytes(input, expected):
    """StatusLine.to_bytes should generate valid status lines."""
    assert bytes(input) == expected
    assert input.to_bytes() == expected


def test_StatusLine_round_trip():
    """StatusLine.from_* should parse the output of StatusLine.to_bytes"""

    expected = P.StatusLine(P.HTTPVersion(1, 1), 200, 'OK')
    assert P.StatusLine.from_bytes(expected.to_bytes()) == expected


@pytest.mark.parametrize(
    'input,expected',
    [('GET / HTTP/1.1',
      P.RequestLine('GET', URL('/'), P.HTTPVersion(1, 1))),

     ('POST http://www.site.com/something?q=abcd HTTP/1.0',
      P.RequestLine(method='POST',
                    url=URL(u'http://www.site.com/something?q=abcd'),
                    version=P.HTTPVersion(major=1, minor=0))),

     ('OPTIONS */* HTTP/1.1',
      P.RequestLine(method='OPTIONS',
                    url=URL(u'*/*'),
                    version=P.HTTPVersion(major=1, minor=1)))])
def test_RequestLine_froms(input, expected):
    """RequestLine.from_* should parse valid request lines."""

    assert P.RequestLine.from_bytes(input) == expected
    matched = P.RequestLine.PARSE_REQUEST_LINE.match(input)
    assert P.RequestLine.from_match(matched) == expected


@pytest.mark.parametrize('input,expected',
                         [(' / HTTP/1.1', P.InvalidMethod),
                          ('GET ` HTTP/1.1', P.InvalidURI),
                          ('!!CompletelyWrong!!', P.InvalidRequestLine)])
def test_RequestLine_froms_raises(input, expected):
    """RequestLine.froms_* should fail to parse invalid request lines."""

    with pytest.raises(expected):
        P.RequestLine.from_bytes(input)

    with pytest.raises(expected):
        m = P.RequestLine.PARSE_REQUEST_LINE.match(input)
        P.RequestLine.from_match(m)


@pytest.mark.parametrize(
    'input,expected',
    [(P.RequestLine(method='GET',
                    url=URL(u'/'),
                    version=P.HTTPVersion(major=1, minor=1)),
      'GET / HTTP/1.1'),

     (P.RequestLine(method='POST',
                    url=URL(u'http://www.site.com/something?q=abcd'),
                    version=P.HTTPVersion(major=1, minor=0)),
      'POST http://www.site.com/something?q=abcd HTTP/1.0'),

     (P.RequestLine(method='OPTIONS',
                    url=URL(u'*/*'),
                    version=P.HTTPVersion(major=1, minor=1)),
      'OPTIONS */* HTTP/1.1')])
def test_RequestLine(input, expected):
    """RequestLine.to_bytes should generate valid request lines."""

    assert bytes(input) == expected
    assert input.to_bytes() == expected


def test_RequestLine_round_trip():
    """RequestLine.from_* should parse the output of RequestLine.to_bytes"""

    expected = P.RequestLine(method='OPTIONS', url=URL(u'*'),
                             version=P.HTTPVersion(1, 1))

    assert P.RequestLine.from_bytes(expected.to_bytes()) == expected


def test_Reader():
    """Readers should enforce the contract for protocol readers."""

    class BrokenReader(P.Reader):
        pass

    with pytest.raises(TypeError):
        BrokenReader()

    class SomeReader(P.Reader):

        def _make_reader(self):
            thing = None
            while True:
                self.state = thing
                thing = yield thing

    reader = SomeReader()
    assert reader.send('ok') == 'ok'
    assert reader.state == 'ok'


def test_Writer():
    """Writers should enforce the protocol writer's contract."""

    class BrokenWriter(P.Writer):
        pass

    with pytest.raises(TypeError):
        BrokenWriter()

    class SomeWriter(P.Writer):

        def _make_writer(self):
            while True:
                self.state = 'ok'
                yield self.state

    writer = SomeWriter()
    writer_iter = iter(writer)
    assert next(writer_iter) == 'ok'
    assert writer.state == 'ok'


_HEADER_LINES = ['Host: www.org.com\n',
                 'Content-Encoding: chunked,\r\n',
                 '  irrelevant\n',
                 'Accept: text/plain\r\n',
                 'Accept: text/html\n']

_HEADER_PARSED = D.Headers([('Host', 'www.org.com'),
                            ('Content-Encoding', 'chunked,  irrelevant'),
                            ('Accept', 'text/plain'),
                            ('Accept', 'text/html')])

_HEADER_EXPECTED_LINES = ['Host: www.org.com\r\n',
                          'Content-Encoding: chunked,  irrelevant\r\n',
                          'Accept: text/plain\r\n',
                          'Accept: text/html\r\n',
                          '\r\n']


def test_HeadersReader():
    reader = P.HeadersReader()
    repr(reader)

    assert reader.state is M.NeedLine

    for line in _HEADER_LINES:
        state = reader.send(M.HaveLine(line))
        assert state is M.NeedLine
        assert reader.state is state

    state = reader.send(M.HaveLine('\n'))
    assert state is M.Complete
    assert reader.state is state
    assert reader.complete

    assert reader.headers == _HEADER_PARSED


def test_HeadersWriter():
    writer = P.HeadersWriter(headers=_HEADER_PARSED)
    repr(writer)
    assert P._flush_writer_to_bytes(writer)
    assert writer.state is M.Complete

    writer = P.HeadersWriter(headers=_HEADER_PARSED)

    for message, expected in izip(iter(writer), _HEADER_EXPECTED_LINES):
        t, actual = message
        assert t == M.HaveLine.type
        assert writer.state is message
        assert actual == expected

    assert writer.complete
