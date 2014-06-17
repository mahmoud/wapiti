# -*- coding: utf-8 -*-

from .compat.dictutils import OMD

HEADER_CASE_MAP = None
ALL_HEADERS, REQUEST_HEADERS, RESPONSE_HEADERS = None, None, None

MAX_HEADER_CASE_ENTRIES = 2048  # arbitrary bound


def _init_headers():
    # called (and del'd) at the very bottom
    global ALL_HEADERS, REQUEST_HEADERS, RESPONSE_HEADERS, HEADER_CASE_MAP
    ALL_HEADERS = (GENERAL_HEADERS + REQUEST_ONLY_HEADERS
                   + RESPONSE_ONLY_HEADERS + ENTITY_HEADERS)
    REQUEST_HEADERS = GENERAL_HEADERS + REQUEST_ONLY_HEADERS + ENTITY_HEADERS
    RESPONSE_HEADERS = GENERAL_HEADERS + RESPONSE_ONLY_HEADERS + ENTITY_HEADERS
    HEADER_CASE_MAP = dict((h.lower(), h) for h in ALL_HEADERS)


GENERAL_HEADERS = ['Cache-Control',
                   'Connection',
                   'Date',
                   'Pragma',
                   'Trailer',
                   'Transfer-Encoding',
                   'Upgrade',
                   'Via',
                   'Warning']

REQUEST_ONLY_HEADERS = ['Accept',
                        'Accept-Charset',
                        'Accept-Encoding',
                        'Accept-Language',
                        'Authorization',
                        'Cookie',  # RFC6265
                        'Expect',
                        'From',
                        'Host',
                        'If-Match',
                        'If-Modified-Since',
                        'If-None-Match',
                        'If-Range',
                        'If-Unmodified-Since',
                        'Max-Forwards',
                        'Proxy-Authorization',
                        'Range',
                        'Referer',
                        'TE',
                        'User-Agent']

RESPONSE_ONLY_HEADERS = ['Accept-Ranges',
                         'Age',
                         'ETag',
                         'Location',
                         'Proxy-Authenticate',
                         'Retry-After',
                         'Server',
                         'Set-Cookie',  # RFC6265
                         'Vary',
                         'WWW-Authenticate']

ENTITY_HEADERS = ['Allow',
                  'Content-Disposition',  # RFC6266
                  'Content-Encoding',
                  'Content-Language',
                  'Content-Length',
                  'Content-Location',
                  'Content-MD5',
                  'Content-Range',
                  'Content-Type',
                  'Expires',
                  'Last-Modified']

HOP_BY_HOP_HEADERS = ['Connection',
                      'Keep-Alive',
                      'Proxy-Authenticate',
                      'TE',
                      'Trailers',
                      'Transfer-Encoding',
                      'Upgrade']


_init_headers()
del _init_headers

CODE_REASONS = OMD([(100, 'Continue'),
                    (101, 'Switching Protocols'),
                    (102, 'Processing'),  # RFC2518
                    (200, 'OK'),
                    (201, 'Created'),
                    (202, 'Accepted'),
                    (203, 'Non-Authoritative Information'),
                    (204, 'No Content'),
                    (205, 'Reset Content'),
                    (206, 'Partial Content'),
                    (300, 'Multiple Choices'),
                    (301, 'Moved Permanently'),
                    (302, 'Found'),
                    (303, 'See Other'),
                    (304, 'Not Modified'),
                    (305, 'Use Proxy'),
                    (307, 'Temporary Redirect'),
                    (400, 'Bad Request'),
                    (401, 'Unauthorized'),
                    (402, 'Payment Required'),
                    (403, 'Forbidden'),
                    (404, 'Not Found'),
                    (405, 'Method Not Allowed'),
                    (406, 'Not Acceptable'),
                    (407, 'Proxy Authentication Required'),
                    (408, 'Request Time-out'),
                    (409, 'Conflict'),
                    (410, 'Gone'),
                    (411, 'Length Required'),
                    (412, 'Precondition Failed'),
                    (413, 'Request Entity Too Large'),
                    (414, 'Request-URI Too Large'),
                    (415, 'Unsupported Media Type'),
                    (416, 'Requested range not satisfiable'),
                    (417, 'Expectation Failed'),
                    (418, "I'm a teapot"),  # RFC2324
                    (422, 'Unprocessable Entity'),  # RFC4918
                    (423, 'Locked'),  # RFC4918
                    (424, 'Failed Dependency'),  # RFC4918
                    (426, 'Upgrade Required'),  # RFC2817
                    (428, 'Precondition Required'),  # RFC6585
                    (429, 'Too Many Requests'),  # RFC6585
                    (431, 'Request Header Fields Too Large'),  # RFC6585
                    (500, 'Internal Server Error'),
                    (501, 'Not Implemented'),
                    (502, 'Bad Gateway'),
                    (503, 'Service Unavailable'),
                    (504, 'Gateway Time-out'),
                    (505, 'HTTP Version not supported'),
                    (507, 'Insufficient Storage'),  # RFC4918
                    (508, 'Loop Detected'),  # RFC5842
                    (510, 'Not Extended'),  # RFC2774
                    (511, 'Network Authentication Required')  # RFC6585
                    ])

REASON_CODES = CODE_REASONS.inverted()


# Headers are foldable if they contain comma-separated values ("1#")
# relevant:
"""
RFC2616 4.2:
Multiple message-header fields with the same field-name MAY be
present in a message if and only if the entire field-value for that
header field is defined as a comma-separated list [i.e., #(values)].
It MUST be possible to combine the multiple header fields into one
"field-name: field-value" pair, without changing the semantics of the
message, by appending each subsequent field-value to the first, each
separated by a comma. The order in which header fields with the same
field-name are received is therefore significant to the
interpretation of the combined field value, and thus a proxy MUST NOT
change the order of these field values when a message is forwarded.
"""
FOLDABLE_HEADERS = ['Accept-Charset',
                    'Accept-Encoding',
                    'Accept-Language',
                    'Accept-Ranges',
                    'Cache-Control',
                    'Connection',
                    'Content-Encoding',
                    'Content-Language',
                    'Expect',
                    'If-Match',
                    'If-None-Match',
                    'Pragma',
                    'Proxy-Authenticate',
                    'Trailer',
                    'Transfer-Encoding',
                    'Upgrade',
                    'Vary',
                    'Via',
                    'Warning',
                    'WWW-Authenticate']
FOLDABLE_HEADER_SET = set(FOLDABLE_HEADERS)
