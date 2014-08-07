# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, QueryLimit
from params import StaticParam, SingleParam
from models import PageInfo
from utils import OperationExample, coerce_namespace


class GetRandom(QueryOperation):
    """
    Fetch random pages using MediaWiki's Special:Random.
    """
    field_prefix = 'grn'
    fields = [StaticParam('generator', 'random'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection'),
              SingleParam('namespace', default='', coerce=coerce_namespace)]
    input_field = None
    output_type = [PageInfo]
    per_query_limit = QueryLimit(10, 20)
    default_limit = 10
    examples = [OperationExample(doc='basic random')]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            page_info = PageInfo.from_query(pid_dict,
                                            source=self.source)
            ret.append(page_info)
        return ret

    def get_cont_str(self, *a, **kw):
        return ''


class GetRandomArticles(GetRandom):
    def __init__(self, *a, **kw):
        kw['namespace'] = 0
        super(GetRandomArticles, self).__init__(*a, **kw)
    examples = [OperationExample(doc='random articles')]


class GetRandomCategories(GetRandom):
    def __init__(self, *a, **kw):
        kw['namespace'] = 14
        super(GetRandomCategories, self).__init__(*a, **kw)
    examples = [OperationExample(doc='random categories')]


class GetRandomFilePages(GetRandom):
    def __init__(self, *a, **kw):
        kw['namespace'] = 6
        super(GetRandomFilePages, self).__init__(*a, **kw)
    examples = [OperationExample(doc='random file pages')]
