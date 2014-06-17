
from datetime import datetime

from hematite.response import Response
from hematite.raw.response import RawResponse


_RESP_200_LINES = ('HTTP/1.1 200 OK',
                   'Date: Tue, 11 Mar 2014 06:29:33 GMT',
                   'Last-Modified: Mon, 10 Mar 2014 01:22:01 GMT',
                   'Server: hematited/1.0',
                   'Expires: Tue, 11 Mar 2014 06:29:34 GMT',
                   'Content-Language: en, mi',
                   'X-Proprietary-Header: lol',
                   '', '')  # required to get trailing CRLF

RESP_200_BYTES = '\r\n'.join(_RESP_200_LINES)


def test_resp_raw_resp():
    raw_resp = RawResponse.from_bytes(RESP_200_BYTES)
    resp = Response.from_raw_response(raw_resp)
    assert isinstance(resp.date, datetime)
    assert isinstance(resp.content_language, list)
    the_bytes = resp.to_bytes()

    assert RESP_200_BYTES == the_bytes


def test_cap_norm():
    raw_resp_str = ('HTTP/1.1 200 OK\r\n'
                    'Last-modified: Mon, 10 Mar 2014 01:22:01 GMT\r\n'
                    '\r\n')
    resp = Response.from_bytes(raw_resp_str)
    assert isinstance(resp.last_modified, datetime)
    resp_str = resp.to_bytes()

    assert 'Last-Modified' in resp_str
    assert len(resp_str) == len(raw_resp_str)


def test_proprietary_dupes():
    raw_resp_str = ('HTTP/1.1 200 OK\r\n'
                    'X-App: lol\r\n'
                    'X-App: lmao\r\n'
                    '\r\n')
    resp = Response.from_bytes(raw_resp_str)
    assert resp.headers['X-App'] == 'lmao'
    resp_str = resp.to_bytes()
    assert resp_str == raw_resp_str


def test_empty_header():
    raw_resp_str = ('HTTP/1.1 200 OK\r\n'
                    'X-Terrible-Header: \r\n'
                    '\r\n')
    resp = Response.from_bytes(raw_resp_str)
    assert resp.headers['X-Terrible-Header'] == ''
    resp_str = resp.to_bytes()
    assert 'X-Terrible' not in resp_str


def test_invalid_expires():
    import datetime
    raw_resp_str = ('HTTP/1.1 200 OK\r\n'
                    'Expires: -1\r\n'
                    '\r\n')
    resp = Response.from_bytes(raw_resp_str)
    assert resp.expires < datetime.datetime.utcnow()
    resp_str = resp.to_bytes()
    assert 'Expires' in resp_str


def test_etag_field():
    resp = Response(200)
    resp.etag = '1234'
    assert resp.etag.tag == '1234'
    assert not resp.etag.is_weak
    resp.etag = None
    assert resp.etag is None


def test_vary_field():
    resp = Response(200)
    resp.vary = 'Content-MD5, Pragma'
    assert len(resp.vary) == 2


def test_content_type():
    resp_bytes = ('HTTP/1.1 200 OK\r\n'
                  'Content-Type: text/html; charset=UTF-8\r\n'
                  '\r\n')
    resp = Response.from_bytes(resp_bytes)
    assert resp.content_type.media_type == 'text/html'
    assert resp.content_type.charset == 'UTF-8'
    data = resp.get_data(as_bytes=False)
    assert isinstance(data, unicode)
    rt_resp_bytes = resp.to_bytes()
    assert 'text/html; charset=UTF-8' in rt_resp_bytes
    repr(resp.content_type)
    resp.content_type.params['lol'] = 'lmao'
    repr(resp.content_type)


def test_content_length_field():
    resp = Response(200)
    resp.content_length = 200
    assert resp.content_length == 200
    resp.content_length = '70'
    assert resp.content_length == 70


def test_content_disposition():
    #resp_bytes = ('HTTP/1.1 200 OK\r\n'
    #              'Content-Disposition: attachment;\r\n'
    #              '                     filename="EURO rates";\r\n'
    #              '                     filename*=utf-8''%e2%82%ac%20rates\r\n'
    #              '\r\n')
    resp_bytes = ('HTTP/1.1 200 OK\r\n'
                  'Content-Disposition: attachment; filename="EURO rates"; filename*=utf-8\'\'%e2%82%ac%20rates\r\n'
                  '\r\n')
    resp = Response.from_bytes(resp_bytes)
    content_disp = resp.content_disposition
    assert content_disp.disp_type == 'attachment'
    assert content_disp.filename == 'EURO rates'
    assert content_disp.filename_ext == "utf-8''%e2%82%ac%20rates"
    assert content_disp.is_attachment
    assert not content_disp.is_inline

    rt_resp_bytes = resp.to_bytes()
    assert 'attachment' in rt_resp_bytes
    repr(resp.content_disposition)
    resp.content_disposition.params['lol'] = 'lmao'
    repr(resp.content_disposition)


def test_status_reason():
    resp = Response(200)
    assert resp.reason == 'OK'
    resp = Response(500)
    assert resp.reason == 'Internal Server Error'
    resp = Response(9000)
    assert resp.reason == ''


def test_retry_after():
    resp = Response(503)
    resp.retry_after = '120'
    assert resp.retry_after.seconds == 120
    assert '120' in resp.to_bytes()


def test_content_range():
    resp = Response(200)
    resp.content_range = 'bytes 0-499/1234'
    cr = resp.content_range
    assert cr.begin == 0
    assert cr.end == 499
    assert cr.total == 1234
    repr(cr)

    cr.begin = None
    assert '*/' in cr.to_bytes()

    resp.content_range = None
    assert not resp.content_range


def test_folding_headers():
    resp_bytes = ('HTTP/1.1 200 OK\r\n'
                  'Cache-Control: must-revalidate\r\n'
                  'Cache-Control: proxy-revalidate\r\n'
                  'Cache-Control: no-cache\r\n'
                  'Content-Type: text/html; charset=UTF-8\r\n'
                  '\r\n')
    resp = Response.from_bytes(resp_bytes)
    rt_headers = resp._get_header_dict()
    cc_expected = 'must-revalidate, proxy-revalidate, no-cache'
    assert rt_headers['Cache-Control'] == cc_expected
