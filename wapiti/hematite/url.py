# -*- coding: utf-8 -*-

import re
import socket
import string

from compat import (unicode, OrderedMultiDict, BytestringHelper)

"""
 - url.params (semicolon separated) http://www.w3.org/TR/REC-html40/appendix/notes.html#h-B.2.2
 - support python compiled without IPv6
 - support empty port (e.g., http://gweb.com:/)
"""

DEFAULT_ENCODING = 'utf-8'

# The unreserved URI characters (per RFC 3986)
_UNRESERVED_CHARS = (frozenset(string.uppercase)
                     | frozenset(string.lowercase)
                     | frozenset(string.digits)
                     | frozenset('-._~'))
_RESERVED_CHARS = frozenset(":/?#[]@!$&'()*+,;=")
_PCT_ENCODING = (frozenset('%')
                 | frozenset(string.digits)
                 | frozenset(string.uppercase[:6])
                 | frozenset(string.lowercase[:6]))
_ALLOWED_CHARS = _UNRESERVED_CHARS | _RESERVED_CHARS | _PCT_ENCODING

# URL parsing regex (per RFC 3986)
_URL_RE = re.compile(r'^((?P<scheme>[^:/?#]+):)?'
                     r'(//(?P<authority>[^/?#]*))?'
                     r'(?P<path>[^?#]*)'
                     r'(\?(?P<query>[^#]*))?'
                     r'(#(?P<fragment>.*))?')

_SCHEME_CHARS = re.escape(''.join(_ALLOWED_CHARS - set(':/?#')))
_AUTH_CHARS = re.escape(''.join(_ALLOWED_CHARS - set(':/?#')))
_PATH_CHARS = re.escape(''.join(_ALLOWED_CHARS - set('?#')))
_QUERY_CHARS = re.escape(''.join(_ALLOWED_CHARS - set('#')))
_FRAG_CHARS = re.escape(''.join(_ALLOWED_CHARS))

_ABS_PATH_RE = (r'(?P<path>[' + _PATH_CHARS + ']*)'
                r'(\?(?P<query>[' + _QUERY_CHARS + ']*))?'
                r'(#(?P<fragment>[' + _FRAG_CHARS + '])*)?')

_URL_RE_STRICT = re.compile(r'^(?:(?P<scheme>[' + _SCHEME_CHARS + ']+):)?'
                            r'(//(?P<authority>[' + _AUTH_CHARS + ']*))?'
                            + _ABS_PATH_RE)


def _make_quote_map(allowed_chars):
    ret = {}
    for i, c in zip(range(256), str(bytearray(range(256)))):
        ret[c] = c if c in allowed_chars else '%{0:02X}'.format(i)
    return ret


_PATH_QUOTE_MAP = _make_quote_map(_ALLOWED_CHARS - set('?#'))
_QUERY_ELEMENT_QUOTE_MAP = _make_quote_map(_ALLOWED_CHARS - set('#&='))


def escape_path(text, to_bytes=True):
    if not to_bytes:
        return u''.join([_PATH_QUOTE_MAP.get(c, c) for c in text])
    try:
        bytestr = text.encode('utf-8')
    except UnicodeDecodeError:
        pass
    except:
        raise ValueError('expected text or UTF-8 encoded bytes, not %r' % text)
    return ''.join([_PATH_QUOTE_MAP[b] for b in bytestr])


def escape_query_element(text, to_bytes=True):
    if not to_bytes:
        return u''.join([_QUERY_ELEMENT_QUOTE_MAP.get(c, c) for c in text])
    try:
        bytestr = text.encode('utf-8')
    except UnicodeDecodeError:
        pass
    except:
        raise ValueError('expected text or UTF-8 encoded bytes, not %r' % text)
    return ''.join([_QUERY_ELEMENT_QUOTE_MAP[b] for b in bytestr])


def parse_authority(au_str):  # TODO: namedtuple?
    user, pw, hostinfo = parse_userinfo(au_str)
    family, host, port = parse_hostinfo(hostinfo)
    return user, pw, family, host, port


def parse_hostinfo(au_str):
    """\
    returns:
      family (socket constant or None), host (string), port (int or None)

    >>> parse_hostinfo('googlewebsite.com:443')
    (None, 'googlewebsite.com', 443)
    >>> parse_hostinfo('[::1]:22')
    (10, '::1', 22)
    >>> parse_hostinfo('192.168.1.1:5000')
    (2, '192.168.1.1', 5000)

    TODO: check validity of non-IP host before returning?
    TODO: exception types for parse exceptions
    """
    family, host, port = None, '', None
    if not au_str:
        return family, host, port
    if ':' in au_str:  # for port-explicit and IPv6 authorities
        host, _, port_str = au_str.rpartition(':')
        if port_str and ']' not in port_str:
            try:
                port = int(port_str)
            except ValueError:
                raise ValueError('invalid authority in URL %r expected int'
                                 ' for port, not %r)' % (au_str, port_str))
        else:
            host, port = au_str, None
        if host and '[' == host[0] and ']' == host[-1]:
            host = host[1:-1]
            try:
                socket.inet_pton(socket.AF_INET6, host)
            except socket.error:
                raise ValueError('invalid IPv6 host: %r' % host)
            else:
                family = socket.AF_INET6
                return family, host, port
    try:
        socket.inet_pton(socket.AF_INET, host)
    except socket.error:
        host = host if (host or port) else au_str
    else:
        family = socket.AF_INET
    return family, host, port


def parse_userinfo(au_str):
    userinfo, _, hostinfo = au_str.partition('@')
    if hostinfo:
        username, _, password = userinfo.partition(':')
    else:
        username, password, hostinfo = None, None, au_str
    return username, password, hostinfo


def parse_url(url_str, encoding=DEFAULT_ENCODING, strict=False):
    if not isinstance(url_str, unicode):
        try:
            url_str = url_str.decode(encoding)
        except AttributeError:
            raise TypeError('parse_url expected str, unicode, or bytes, not %r'
                            % url_str)
    um = (_URL_RE_STRICT if strict else _URL_RE).match(url_str)
    try:
        gs = um.groupdict()
    except AttributeError:
        raise ValueError('could not parse url: %r' % url_str)
    if gs['authority']:
        try:
            gs['authority'] = gs['authority'].decode('idna')
        except:
            pass
    else:
        gs['authority'] = ''
    user, pw, family, host, port = parse_authority(gs['authority'])
    gs['username'] = user
    gs['password'] = pw
    gs['family'] = family
    gs['host'] = host
    gs['port'] = port
    return gs


class QueryArgDict(OrderedMultiDict):
    # TODO: caching
    # TODO: self.update_extend_from_string()?

    @classmethod
    def from_string(cls, query_string):
        pairs = parse_qsl(query_string, keep_blank_values=True)
        return cls(pairs)

    def to_bytes(self):
        # note: uses '%20' instead of '+' for spaces, based partially
        # on observed behavior in chromium.
        ret_list = []
        for k, v in self.iteritems(multi=True):
            key = escape_query_element(unicode(k), to_bytes=True)
            if v is None:
                ret_list.append(key)
                continue
            val = escape_query_element(unicode(v), to_bytes=True)
            ret_list.append('='.join((key, val)))
        return '&'.join(ret_list)

    def to_text(self):
        ret_list = []
        for k, v in self.iteritems(multi=True):
            key = escape_query_element(unicode(k), to_bytes=False)
            if v is None:
                ret_list.append(key)
                continue
            val = escape_query_element(unicode(v), to_bytes=False)
            ret_list.append(u'='.join((key, val)))
        return u'&'.join(ret_list)


# TODO: naming: 'args', 'query_args', or 'query_params'?

class URL(BytestringHelper):
    _attrs = ('scheme', 'username', 'password', 'family',
              'host', 'port', 'path', 'query', 'fragment')
    _quotable_attrs = ('username', 'password', 'path', 'query')  # fragment?

    def __init__(self, url_str=None, encoding=None, strict=False):
        encoding = encoding or DEFAULT_ENCODING
        # TODO: encoded query strings have an encoding behind the
        # percent-escaping, but otherwise is this member necessary?
        # if not, be more explicit
        self.encoding = encoding
        url_dict = {}
        if url_str:
            url_dict = parse_url(url_str, encoding=encoding, strict=strict)

        _d = unicode()
        self.params = _d  # TODO: support path params?
        for attr in self._attrs:
            val = url_dict.get(attr, _d) or _d
            if attr in self._quotable_attrs and '%' in val:
                val = unquote(val)
            setattr(self, attr, val)
        self.args = QueryArgDict.from_string(self.query)

    @property
    def is_absolute(self):
        return bool(self.scheme)  # RFC2396 3.1

    @property
    def http_request_url(self):  # TODO: name
        parts = [escape_path(self.path)]
        query_string = self.get_query_string(to_bytes=True)
        if query_string:
            parts.append(query_string)
        return '?'.join(parts)

    @property
    def http_request_host(self):  # TODO: name
        ret = []
        host = self.host.encode('idna')
        if self.family == socket.AF_INET6:
            ret.extend(['[', host, ']'])
        else:
            ret.append(host)
        if self.port:
            ret.extend([':', unicode(self.port)])
        return ''.join(ret)

    def __iter__(self):
        s = self
        return iter((s.scheme, s.get_authority(idna=True), s.path,
                     s.params, s.get_query_string(to_bytes=True), s.fragment))

    # TODO: normalize?

    def get_query_string(self, to_bytes=True):
        if to_bytes:
            return self.args.to_bytes()
        return self.args.to_text()

    def get_authority(self, idna=True):
        parts = []
        _add = parts.append
        if self.username:
            _add(self.username)
            if self.password:
                _add(':')
                _add(self.password)
            _add('@')
        if self.host:
            if self.family == socket.AF_INET6:
                _add('[')
                _add(self.host)
                _add(']')
            elif idna:
                _add(self.host.encode('idna'))
            else:
                _add(self.host)
            if self.port:
                _add(':')
                _add(unicode(self.port))
        return u''.join(parts)

    def to_text(self, display=False):
        """\
        This method takes the place of urlparse.urlunparse/urlunsplit.
        It's a tricky business.
        """
        full_encode = (not display)
        scheme, path, params = self.scheme, self.path, self.params
        authority = self.get_authority(idna=full_encode)
        query_string = self.get_query_string(to_bytes=full_encode)
        fragment = self.fragment

        parts = []
        _add = parts.append
        if scheme:
            _add(scheme)
            _add(':')
        if authority:
            _add('//')
            _add(authority)
        elif (scheme and path[:2] != '//'):
            _add('//')
        if path:
            if parts and path[:1] != '/':
                _add('/')
            _add(escape_path(path, to_bytes=full_encode))
        if params:
            _add(';')
            _add(params)
        if query_string:
            _add('?')
            _add(query_string)
        if fragment:
            _add('#')
            _add(fragment)
        return u''.join(parts)

    def to_bytes(self):
        return self.to_text().encode('utf-8')

    @classmethod
    def from_bytes(cls, bytestr):
        return cls(bytestr)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.to_text())

    def __eq__(self, other):
        for attr in self._attrs:
            if not getattr(self, attr) == getattr(other, attr, None):
                return False
        return True

    def __ne__(self, other):
        return not self == other


_hexdig = '0123456789ABCDEFabcdef'
_hextochr = dict((a + b, chr(int(a + b, 16)))
                 for a in _hexdig for b in _hexdig)
_asciire = re.compile('([\x00-\x7f]+)')


def unquote(s, encoding=DEFAULT_ENCODING):
    "unquote('abc%20def') -> 'abc def'. aka percent decoding."
    if isinstance(s, unicode):
        if '%' not in s:
            return s
        bits = _asciire.split(s)
        res = [bits[0]]
        append = res.append
        for i in range(1, len(bits), 2):
            if '%' in bits[i]:
                append(unquote(str(bits[i])).decode(encoding))
            else:
                append(bits[i])
            append(bits[i + 1])
        return u''.join(res)

    bits = s.split('%')
    if len(bits) == 1:
        return s
    res = [bits[0]]
    append = res.append
    for item in bits[1:]:
        try:
            append(_hextochr[item[:2]])
            append(item[2:])
        except KeyError:
            append('%')
            append(item)
    return ''.join(res)


def parse_qsl(qs, keep_blank_values=True, encoding=DEFAULT_ENCODING):
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    ret = []
    for pair in pairs:
        if not pair:
            continue
        key, _, value = pair.partition('=')
        if not value:
            if keep_blank_values:
                value = ''
            else:
                continue
        if value or keep_blank_values:
            # TODO: really always convert plus signs to spaces?
            key = unquote(key.replace('+', ' '))
            value = unquote(value.replace('+', ' '))
            ret.append((key, value))
    return ret
