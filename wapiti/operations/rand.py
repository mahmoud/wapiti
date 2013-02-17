# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import SubjectResolvingQueryOperation, StaticParam
from base import DEFAULT_RETRIES
from models import PageIdentifier


class GetRandom(SubjectResolvingQueryOperation):
    field_prefix = 'grn'
    fields = [StaticParam('generator', 'random'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    query_field = None  # hmm

    def __init__(self, limit, retries=DEFAULT_RETRIES, **kw):
        # TODO: removed query arg parameter, random doesn't need it, but is
        # there a less ugly way?
        super(GetRandom, self).__init__(None, limit, retries, **kw)

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret

    def get_cont_str(self, *a, **kw):
        return ''
