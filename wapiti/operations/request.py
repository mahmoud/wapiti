# -*- coding: utf-8 -*-

import sys
from os.path import dirname, abspath
# just until ransom becomes its own package
sys.path.append(dirname(dirname(abspath(__file__))))

import json

from hematite import client as hematite_client

DEFAULT_API_URL = 'http://en.wikipedia.org/w/api.php'
DEFAULT_BASE_URL = 'http://en.wikipedia.org/wiki/'
DEFAULT_USER_AGENT = 'Wapiti/0.0.0 Mahmoud Hashemi mahmoud@hatnote.com'

DEFAULT_WEB_CLIENT = hematite_client.Client(user_agent=DEFAULT_USER_AGENT)
BASE_API_PARAMS = {'format': 'json',
                   'servedby': 'true'}


class WapitiException(Exception):
    pass


class MWResponse(hematite_client.ClientResponse):
    def __init__(self, params, **kw):
        # These settings will all go on the WapitiClient
        self.raise_exc = kw.pop('raise_exc', True)
        self.raise_err = kw.pop('raise_err', True)
        self.raise_warn = kw.pop('raise_warn', False)
        self.client = kw.pop('client')
        self.web_client = getattr(self.client,
                                  'web_client',
                                  DEFAULT_WEB_CLIENT)
        if kw:
            raise ValueError('got unexpected keyword arguments: %r'
                             % kw.keys())
        self.api_url = self.client.api_url
        params = params or {}
        self.params = dict(BASE_API_PARAMS)
        self.params.update(params)
        self.action = params['action']

        self.results = None
        self.servedby = None
        self.exception = None
        self.error = None
        self.error_code = None
        self.warnings = []
        self.notices = []  # TODO: remove

        request = hematite_client.Request(method='GET', url=self.api_url)
        request._url.args.update(self.params)
        super(MWResponse, self).__init__(client=self.web_client,
                                         request=request)

    def do_complete(self):
        # TODO: add URL to all exceptions
        #self.exception = e  # TODO: wrap
        #    if self.raise_exc:
        #        raise
        #    return self
        try:
            self.results = json.loads(self.get_data())
        except Exception as e:
            self.results = None
            self.exception = e  # TODO: wrap
            if self.raise_exc:
                raise
            return
        self.servedby = self.results.get('servedby')

        error = self.results.get('error')
        if error:
            self.error = error.get('info')
            self.error_code = error.get('code')

        warnings = self.results.get('warnings', {})
        for mod_name, warn_dict in warnings.items():
            warn_str = '%s: %s' % (mod_name, warn_dict.get('*', warn_dict))
            self.warnings.append(warn_str)

        if self.error and self.raise_err:
            raise WapitiException(self.error_code)
        if self.warnings and self.raise_warn:
            raise WapitiException('warnings: %r' % self.warnings)
        return self
