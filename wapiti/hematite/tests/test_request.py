# -*- coding: utf-8 -*-

from hematite.request import Request

BASIC_REQ = '\r\n'.join(['GET /html/rfc3986 HTTP/1.1',
                         'Host: tooxols.ietf.org',
                         '\r\n'])

WP_REQ = ('GET /wiki/Beyonc%C3%A9%20Knowles HTTP/1.1',
          'Host: en.wikipedia.org',
          'Connection: keep-alive',
          'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.22 (KHTML, like Gecko) Ubuntu Chromium/25.0.1364.160 Chrome/25.0.1364.160 Safari/537.22',
          'Accept-Encoding: gzip,deflate,sdch',
          'Accept-Language: en-US,en;q=0.8',
          'Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.3',
          'Cookie: centralnotice_bucket=1-4.2; centralnotice_bannercount_fr12=1',
          '\r\n')
WP_REQ = '\r\n'.join(WP_REQ)


def _cmpable_req(req_text):
    req_lower = req_text.lower()
    header, _, body = req_lower.partition('\r\n\r\n')
    header_lines = header.rstrip().splitlines()
    ret = [header_lines[0]]
    ret.extend(sorted(header_lines[1:]))
    ret.append('\r\n')
    ret = '\r\n'.join(ret)
    return ret + body


def test_basic_req_url():
    req = Request.from_bytes(BASIC_REQ)
    assert req.url.encode() == 'http://tooxols.ietf.org/html/rfc3986'


def test_basic_req():
    req = Request.from_bytes(BASIC_REQ)
    assert req.to_bytes() == BASIC_REQ


def test_wikipedia_req():
    req = Request.from_bytes(WP_REQ)
    assert req.connection == 'keep-alive'
    re_req = req.to_bytes()
    assert _cmpable_req(re_req) == _cmpable_req(WP_REQ)
