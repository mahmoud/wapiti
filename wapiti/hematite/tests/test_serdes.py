# -*- coding: utf-8 -*-

from hematite.serdes import (content_range_spec_from_bytes,
                             content_range_spec_to_bytes,
                             content_header_from_bytes,
                             accept_header_from_bytes,
                             items_header_from_bytes,
                             list_header_from_bytes,
                             retry_after_from_bytes,
                             retry_after_to_bytes,
                             range_spec_from_bytes,
                             range_spec_to_bytes,
                             http_date_from_bytes)


_ACCEPT_TESTS = [('', []),
                 (' ', []),

                 # Accept
                 ('audio/*; q=0.2 , audio/basic', [('audio/*', 0.2), ('audio/basic', 1.0)]),
                 ('text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                  [('text/html', 1.0), ('application/xhtml+xml', 1.0),
                   ('application/xml', 0.9), ('image/webp', 1.0), ('*/*', 0.8)]),

                 # Accept-Charset
                 ('iso-8859-5, unicode-1-1;q=0.8',
                  [('iso-8859-5', 1.0), ('unicode-1-1', 0.8)]),

                 # Accept-Encoding
                 ('*',  [('*', 1.0)]),
                 ('compress, gzip', [('compress', 1.0), ('gzip', 1.0)]),
                 ('compress;q=0.5, gzip;q=1.0', [('compress', 0.5), ('gzip', 1.0)]),
                 ('gzip;q=1.0, identity; q=0.5, *;q=0', [('gzip', 1.0), ('identity', 0.5), ('*', 0.0)]),

                 # Accept-Language
                 ('da, en-gb;q=0.8, en;q=0.7', [('da', 1.0), ('en-gb', 0.8), ('en', 0.7)]),

                 # Accept-Ranges
                 ('bytes', [('bytes', 1.0)]),
                 ('none', [('none', 1.0)])]


def test_accept_from_bytes():
    for serialized, expected in _ACCEPT_TESTS:
        deserialized = accept_header_from_bytes(serialized)
        assert deserialized == expected


_ITEMS_TESTS = [('', []),
                (' ', []),

                # WWW-Authenticate
                ('Basic realm="myRealm"', [('Basic realm', 'myRealm')]),

                # Cache control
                ('private, community="UCI"', [('private', None), ('community', 'UCI')])]


def test_items_from_bytes():
    for serialized, expected in _ITEMS_TESTS:
        deserialized = items_header_from_bytes(serialized)
        assert deserialized == expected


_LIST_TESTS = [('', []),
               (' ', []),
               ('mi, en', ['mi', 'en'])]


def test_list_from_bytes():
    for serialized, expected in _LIST_TESTS:
        deserialized = list_header_from_bytes(serialized)
        assert deserialized == expected


_DATE_TESTS = [('Sun, 06 Nov 1994 08:49:37 GMT', '1994-11-06 08:49:37'),
               ('Sunday, 06-Nov-94 08:49:38 GMT', '1994-11-06 08:49:38'),
               ('Sun Nov  6 08:49:39 1994', '1994-11-06 08:49:39')]


def test_http_date_from_bytes():
    for serialized, expected in _DATE_TESTS:
        deserialized = http_date_from_bytes(serialized)
        assert str(deserialized) == expected


_CONTENT_TESTS = [('', ('', [])),
                  (' ', ('', [])),
                  ('text/plain', ('text/plain', [])),
                  ('text/html; charset=ISO-8859-4',
                   ('text/html', [('charset', 'ISO-8859-4')]))]

_ruff_content_h = ('message/external-body; access-type=URL;'
                   ' URL*0="ftp://";'
                   ' URL*1="cs.utk.edu/pub/moore/bulk-mailer/bulk-mailer.tar"')
_ruff_content_e = ('message/external-body',
                   [('access-type', 'URL'),
                    ('URL*0', 'ftp://'),
                    ('URL*1', 'cs.utk.edu/pub/moore/bulk-mailer/bulk-mailer.tar')])
_CONTENT_TESTS.append((_ruff_content_h, _ruff_content_e))


def test_content_from_bytes():
    for serialized, expected in _CONTENT_TESTS:
        deserialized = content_header_from_bytes(serialized)
        assert deserialized == expected


VALID_BYTES_RANGE_SPECIFIERS = ['bytes=0-499',
                                'bytes=500-999',
                                'bytes=-500',
                                'bytes=9500-',
                                'bytes=0-0,-1',
                                'bytes=500-600,601-999',
                                'bytes=500-700,601-999']


def test_valid_bytes_range_specifiers():
    for r_str in VALID_BYTES_RANGE_SPECIFIERS:
        r_spec = range_spec_from_bytes(r_str)
        assert r_spec[0] == 'bytes'
        assert r_spec[1] and all(r_spec[1:])

        rt_spec_str = range_spec_to_bytes(r_spec)
        assert rt_spec_str == r_str


VALID_CONTENT_RANGES = ['bytes 0-499/1234',
                        'bytes 500-999/1234',
                        'bytes 500-1233/1234',
                        'bytes 734-1233/1234',
                        'bytes 5000-5001/*']


def test_valid_content_ranges():
    for cr_str in VALID_CONTENT_RANGES:
        cr_spec = content_range_spec_from_bytes(cr_str)
        assert cr_spec[0] == 'bytes'
        assert cr_spec[-1]

        rt_cr_str = content_range_spec_to_bytes(cr_spec)
        assert rt_cr_str == cr_str


VALID_RETRY_AFTERS = ['Fri, 31 Dec 1999 23:59:59 GMT',
                      '120']


def test_valid_retry_afters():
    for ra_str in VALID_RETRY_AFTERS:
        ra_obj = retry_after_from_bytes(ra_str)
        assert ra_obj

        rt_ra_str = retry_after_to_bytes(ra_obj)
        assert ra_str == rt_ra_str
