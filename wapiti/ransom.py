# -*- coding: utf-8 -*-
"""
This is like a mini version of requests, which has simply
grown too heavy and presented multiple compatibility issues
re: api changes and gevent.
"""
import urllib2
import gzip

from compat import (unicode, bytes, OrderedDict, StringIO,
                    urlparse, urlunparse, urlencode, requote)


DEFAULT_CONFIG = {
    'headers': {'User-Agent': 'reqs/0.0.0'}}


class Response(object):
    """
    echoing the tone of the rest of the module, this is abysmally
    oversimplified and will be improved soon.
    """
    def __init__(self, status_code=None, text=None, headers=None, error=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers
        self.error = error


def get_items(iterable):
    if not iterable:
        return []
    return OrderedDict(iterable).items()


def get_keys(iterable):
    if not iterable:
        return []
    return OrderedDict(iterable).keys()


def is_iterable(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, basestring)


def get_encoded(val):
    if isinstance(val, bytes):
        val = val.encode('utf-8')
    return val


def ordered_yield(mapping, keys):
    for k in keys:
        try:
            yield (k, mapping.pop(k))
        except KeyError:
            pass
    for k in mapping:
        yield (k, mapping.pop(k))


def parse_url(url):
    try:
        url = unicode(url)
    except UnicodeDecodeError:
        pass

    parsed = urlparse(url)
    if not (parsed.scheme and parsed.netloc):
        raise ValueError("invalid URL, no schema supplied: %r" % url)

    try:
        dec_netloc = parsed.netloc.encode('idna').decode('utf-8')
        parsed = parsed._replace(netloc=dec_netloc)
    except UnicodeError:
        raise ValueError('invalid characters in url: %r' % parsed.netloc)

    if not parsed.path:
        parsed = parsed._replace(path=u'/')

    for k, v in parsed._asdict().items():
        parsed = parsed._replace(**{k: get_encoded(v)})

    return parsed


def encode_url_params(params, keep_blank=False):
    # TODO: handle case where params is just a string
    res = []
    for k, vs in get_items(params):
        if not is_iterable(vs):
            vs = [vs]
        for v in vs:
            if not v:
                if keep_blank:
                    v = ''
                else:
                    continue
            res.append((get_encoded(k), get_encoded(v)))
    return urlencode(res, doseq=True)


# TODO: merging url params
"""
, keep_order=True):
    if keep_order:
        existing_params = parse_qsl(parsed_url.query,
                                    keep_blank_values=True)
        params = list(ordered_yield(params, get_keys(existing_params)))
        query = encode_url_params(params)
    else:
"""


def construct_url(url, params):
    parsed_url = parse_url(url)
    query = parsed_url.query
    encoded_params = encode_url_params(params)
    if encoded_params:
        if query:
            query = query + u'&' + encoded_params
        else:
            query = encoded_params
    new_url = parsed_url._replace(query=query)

    return requote(urlunparse(new_url))


def gunzip(text):
    buf = StringIO(text)
    f = gzip.GzipFile(fileobj=buf)
    return f.read()


class Client(object):
    def __init__(self, config=None):  # among other things
        self.config = dict(DEFAULT_CONFIG)
        if config:
            self.config.update(config)

    def req(self, method, url, params=None, headers=None, use_gzip=True):
        _headers = dict(self.config.get('headers', {}))
        if headers:
            _headers.update(headers)
        headers = _headers
        if use_gzip and not headers.get('Accept-encoding'):
            headers['Accept-encoding'] = 'gzip'

        full_url = construct_url(url, params)
        print full_url
        ret = Response()
        resp_text = None
        resp_status = None
        resp_headers = {}
        try:
            req = urllib2.Request(full_url, headers=headers)
            resp = urllib2.urlopen(req)
            resp_text = resp.read()
            resp.close()
            if 'gzip' in resp.info().get('Content-Encoding', ''):  # TODO
                comp_resp_text = resp_text
                resp_text = gunzip(resp_text)
            resp_status = resp.getcode()
            resp_headers = resp.headers
        except Exception as e:
            raise
        ret.text = resp_text
        ret.status_code = resp_status
        ret.headers = resp_headers
        return ret

    def get(self, url, params=None, headers=None, use_gzip=True):
        return self.req('get', url, params, headers, use_gzip)

    def post(self, url, params=None, headers=None, use_gzip=True):
        return self.req('post', url, params, headers, use_gzip)


requests = Client()


if __name__ == '__main__':
    print requests.get('https://www.google.com/webhp', params={'q':'python double encode unicode'}).text
