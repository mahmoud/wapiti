# -*- coding: utf-8 -*-


class Cookie(object):
    def __init__(self, name, value='', max_age=None, expires=None,
                 path='/', domain=None, secure=None, http_only=False):
        self.name = name
        self.value = value
        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.secure = secure
        self.http_only = http_only

        # other "flags" (properties):
        # - persistent
        # - host-only

    @classmethod
    def from_bytes(cls, bytestr):
        # from a Set-Cookie header
        return cls(bytestr)  # TODO

    def to_bytes(self):
        return self.key  # TODO


class CookieStore(object):
    def __init__(self, cookies=None):
        self.per_domain_limit = 50
        self.total_limit = 3000
        self.cookies = cookies or {}
        self._last_access_times = {}

    def update(self, other):
        """
        for oc in other:
            if oc.name in self:
                # also match domain, path
                # update new cookie with old cookie's creation time
        """

    def eviction_sweep(self):
        # expired
        # exceeds domain limit
        # the rest, in order of least-recent last-access time
        pass

    def get_cookies(self, domain, path, etc):
        pass

    def get_cookie_header(self, domain, path, etc):
        cookies = self.get_cookies(domain, path, etc)
        return '; '.join(['='.join([c.name, c.value]) for c in cookies])
