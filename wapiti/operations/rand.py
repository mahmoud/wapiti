# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, QueryLimit
from params import StaticParam
from models import PageInfo
from utils import OperationExample


class GetRandom(QueryOperation):
    """
    Fetch random pages using MediaWiki's Special:Random.
    """
    field_prefix = 'grn'
    fields = [StaticParam('generator', 'random'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    input_field = None
    output_type = [PageInfo]
    per_query_limit = QueryLimit(10, 20)
    examples = [OperationExample('basic random')]

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
    fields = GetRandom.fields + [StaticParam('grnnamespace', '0')]
    examples = [OperationExample('random articles')]


class GetRandomCategories(GetRandom):
    fields = GetRandom.fields + [StaticParam('grnnamespace', '14')]
    examples = [OperationExample('random categories')]


class GetRandomFilePages(GetRandom):
    fields = GetRandom.fields + [StaticParam('grnnamespace', '6')]
    examples = [OperationExample('random file pages')]
