# -*- coding: utf-8 -*-
import sys

is_py2 = sys.version_info[0] == 2
is_py3 = sys.version_info[0] == 3

from dictutils import OrderedMultiDict, OMD
from io import StringIO


def make_BytestringHelperMeta(target):
    class BytestringHelperMeta(type):
        def __new__(cls, name, bases, attrs):
            if 'to_bytes' in attrs:
                attrs[target] = attrs['to_bytes']
            return super(BytestringHelperMeta, cls).__new__(cls, name,
                                                            bases, attrs)
    return BytestringHelperMeta

if is_py2:
    from urllib import quote, unquote, quote_plus, unquote_plus, urlencode
    from urlparse import urlparse, urlunparse, urljoin, urlsplit, urldefrag
    from urlparse import parse_qsl
    from urllib2 import parse_http_list
    import cookielib
    from Cookie import Morsel
    from ._py2_socketio import SocketIO

    BytestringHelperMeta = make_BytestringHelperMeta(target='__str__')

    unicode, str, bytes, basestring = unicode, str, str, basestring
elif is_py3:
    from urllib.parse import (urlparse, urlunparse, urljoin, urlsplit,
                              urlencode, quote, unquote, quote_plus,
                              unquote_plus, urldefrag, parse_qsl)
    from urllib.request import parse_http_list
    from http import cookiejar as cookielib
    from http.cookies import Morsel
    from socket import SocketIO

    BytestringHelperMeta = make_BytestringHelperMeta(target='__bytes__')

    unicode, str, bytes, basestring = str, bytes, bytes, str
else:
    raise NotImplementedError('welcome to the future, I guess. (report this)')


BytestringHelper = BytestringHelperMeta('BytestringHelper', (object,), {})


# from boltons
def make_sentinel(name='_MISSING', var_name=None):
    class Sentinel(object):
        def __init__(self):
            self.name = name
            self.var_name = var_name
        def __repr__(self):
            if self.var_name:
                return self.var_name
            return '%s(%r)' % (self.__class__.__name__, self.name)
        if var_name:
            def __reduce__(self):
                return self.var_name
        def __nonzero__(self):
            return False
    return Sentinel()
