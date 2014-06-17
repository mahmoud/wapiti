
import io


def io_open(path):
    return io.open(path, mode='rb')


def test_RawResponse_from_bytes_with_google(file_fixture):

    with file_fixture('google.txt', open=io_open) as f:
        resp = RawResponse.from_io(f)

        assert resp.status_line == ((1, 1), 301, 'Moved Permanently')

        expected_headers = [('Location', 'http://www.google.com/'),
                            ('Content-Type', 'text/html; charset=UTF-8'),
                            ('Date', 'Sat, 01 Mar 2014 23:10:17 GMT'),
                            ('Expires', 'Mon, 31 Mar 2014 23:10:17 GMT'),
                            ('Cache-Control', 'public, max-age=2592000'),
                            ('Server', 'gws'),
                            ('Content-Length', '219'),
                            ('X-XSS-Protection', '1; mode=block'),
                            ('X-Frame-Options', 'SAMEORIGIN'),
                            ('Alternate-Protocol', '80:quic'),
                            ('Connection', 'close')]

        assert resp.headers.items() == expected_headers

        expected_body = (
            '<HTML><HEAD><meta http-equiv="content-type"'
            ' content="text/html;charset=utf-8">\n'
            '<TITLE>301 Moved</TITLE></HEAD><BODY>\n'
            '<H1>301 Moved</H1>\n'
            'The document has moved\n'
            '<A HREF="http://www.google.com/">here</A>.\r\n'
            '</BODY></HTML>'
            '\r\n')

        assert resp.body.read() == expected_body


def test_RawResponse_to_bytes(file_fixture):
    with file_fixture('normalized_google_headers.txt',
                      open=io_open) as f:
        expected = io.BytesIO(f.read())
        actual = io.BytesIO()
        f.seek(0)
        resp = RawResponse.from_io(f)
        resp.to_io(actual)
        assert expected.getvalue() == actual.getvalue()
