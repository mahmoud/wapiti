# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, QueryLimit
from params import StaticParam
from models import PageIdentifier
from utils import OperationExample, len_eq

class GetRandom(QueryOperation):
    """
    Fetch random pages using MediaWiki's Special:Random.
    """
    field_prefix = 'grn'
    fields = [StaticParam('generator', 'random'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    input_field = None
    output_type = [PageIdentifier]
    per_query_limit = QueryLimit(10, 20)
    examples = [OperationExample(test=len_eq)]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query(pid_dict,
                                                       source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret

    def get_cont_str(self, *a, **kw):
        return ''
