# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from models import CategoryInfo, PageIdentifier


class GetCategory(QueryOperation):
    param_prefix = 'gcm'
    query_param_name = param_prefix + 'title'
    query_param_prefix = 'Category:'
    static_params = {'generator': 'categorymembers',
                     'prop': 'info',
                     'inprop': 'title|pageid|ns|subjectid|protection'}

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageIdentifier.from_query(pid_dict, self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetSubcategoryInfos(QueryOperation):
    param_prefix = 'gcm'
    static_params = {'generator': 'categorymembers',
                     'prop': 'categoryinfo',
                     'gcmtype': 'subcat'}
    query_param_name = param_prefix + 'title'
    query_param_prefix = 'Category:'

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                cat_info = CategoryInfo.from_query(pid_dict, self.source)
            except ValueError:
                continue
            if cat_info.page_id < 0:
                continue
            ret.append(cat_info)
        return ret
