# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import deque
from base import (QueryOperation,
                  BaseQueryOperation,
                  CompoundQueryOperation,
                  NoMoreResults,
                  PriorityQueue,
                  MAX_LIMIT,
                  StaticParam,
                  SingleParam,
                  MultiParam)
from models import CategoryInfo, PageIdentifier


class GetCategory(QueryOperation):
    field_prefix = 'gcm'
    query_field = SingleParam('title', val_prefix='Category:', required=True)
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'title|pageid|ns|subjectid|talkid|protection')]

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
    field_prefix = 'gcm'
    query_field = SingleParam('title', val_prefix='Category:', required=True)
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'categoryinfo'),
              StaticParam('gcmtype', 'subcat')]

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


class GetFlattenedCategory(CompoundQueryOperation):
    bijective = False
    multiargument = False

    suboperation_type = GetSubcategoryInfos

    def __init__(self, query_param, *a, **kw):
        super(GetFlattenedCategory, self).__init__(query_param, *a, **kw)
        self.seen_cat_names = set([query_param])

    def store_results(self, results):
        for cat_info in results:
            title = cat_info.title
            if title in self.seen_cat_names:
                continue
            self.seen_cat_names.add(title)
            self.results.append(cat_info)
            if cat_info.subcat_count:
                priority = cat_info.subcat_count
                subop = GetSubcategoryInfos(title, self)
                self.suboperations.add(subop, priority)
        return results


class GetCategoryRecursive(CompoundQueryOperation):
    bijective = False
    multiargument = False

    default_generator = GetFlattenedCategory
    suboperation_type = GetCategory
    suboperation_params = {'query_param': lambda ci: ci.title,
                           'priority': lambda ci: ci.page_count}

    def __init__(self, query_param, *a, **kw):
        super(GetCategoryRecursive, self).__init__(query_param, *a, **kw)
        self.seen_titles = set([query_param])

    def store_results(self, results):
        for page_ident in results:
            title = page_ident.title
            if title in self.seen_titles:
                continue
            self.seen_titles.add(title)
            self.results.append(page_ident)
        return results
