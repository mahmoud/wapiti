# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, DEFAULT_RETRIES
from models import PageIdentifier


class GetRandom(QueryOperation):
    param_prefix = 'grn'
    static_params = {'generator': 'random',
                     'prop': 'info',
                     'inprop': 'subjectid|protection'}
    query_param_name = param_prefix + 'title'

    def __init__(self, limit, namespaces=None, retries=DEFAULT_RETRIES, **kw):
        # TODO: removed query arg parameter, random doesn't need it, but is
        # there a less ugly way?
        super(GetRandom, self).__init__(None, limit, namespaces, retries, **kw)

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query_result(pid_dict,
                                                              self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret

    def get_cont_str(self, *a, **kw):
        return ''
