# -*- coding: utf-8 -*-
import sys

is_py2 = sys.version_info[0] == 2
is_py3 = sys.version_info[0] == 3

from collections import OrderedDict  # TODO

if is_py2:
    from urllib import quote, unquote, quote_plus, unquote_plus, urlencode
    from urlparse import urlparse, urlunparse, urljoin, urlsplit, urldefrag
    from urllib2 import parse_http_list
    import cookielib
    from Cookie import Morsel
    from StringIO import StringIO

    unicode, str, bytes = unicode, str, str
elif is_py3:
    from urllib.parse import (urlparse, urlunparse, urljoin, urlsplit,
                              urlencode, quote, unquote, quote_plus,
                              unquote_plus, urldefrag)
    from urllib.request import parse_http_list
    from http import cookiejar as cookielib
    from http.cookies import Morsel
    from io import StringIO

    unicode, str, bytes = str, bytes, bytes
else:
    raise NotImplemented  # 'welcome to the future, I guess'

# The unreserved URI characters (RFC 3986)
UNRESERVED_SET = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    + "0123456789-._~")


def unquote_unreserved(uri):
    """Un-escape any percent-escape sequences in a URI that are unreserved
    characters. This leaves all reserved, illegal and non-ASCII bytes encoded.
    """
    parts = uri.split('%')
    for i in range(1, len(parts)):
        h = parts[i][0:2]
        if len(h) == 2 and h.isalnum():
            c = chr(int(h, 16))
            if c in UNRESERVED_SET:
                parts[i] = c + parts[i][2:]
            else:
                parts[i] = '%' + parts[i]
        else:
            parts[i] = '%' + parts[i]
    return ''.join(parts)


def requote(uri):
    return quote(unquote_unreserved(uri), safe="!#$%&'()*+,/:;=?@[]~")
