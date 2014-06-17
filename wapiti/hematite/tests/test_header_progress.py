# -*- coding: utf-8 -*-

"""
A silly temporary "test" for the convenience of seeing which headers
aren't yet supported.
"""

from pprint import pformat

from hematite.fields import (RESPONSE_FIELDS,
                             HTTP_REQUEST_FIELDS)
from hematite.constants import (REQUEST_HEADERS,
                                RESPONSE_HEADERS)


def test_request_headers_unimpl():
    unimpl = list(REQUEST_HEADERS)
    for field in HTTP_REQUEST_FIELDS:
        if field.http_name in unimpl:
            unimpl.remove(field.http_name)
    print
    print 'Unimplemented Request Headers:'
    print pformat(unimpl)
    print



def test_response_headers_unimpl():
    unimpl = list(RESPONSE_HEADERS)
    for field in RESPONSE_FIELDS:
        if field.http_name in unimpl:
            unimpl.remove(field.http_name)
    print
    print 'Unimplemented Response Headers:'
    print pformat(unimpl)
    print
