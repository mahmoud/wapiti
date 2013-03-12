# -*- coding: utf-8 -*-
"""
    wapiti.operations.category
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    A module of query operations related to categories. MediaWiki categories
    create an automatic index based on category tags in the page text.
"""
from __future__ import unicode_literals

from models import CategoryInfo, PageInfo
from base import (QueryOperation,
                  Operation,
                  Recursive,
                  Tune)
from params import StaticParam, SingleParam, MultiParam
from utils import OperationExample


class GetCategoryList(QueryOperation):
    """
    Fetch the categories containing pages.
    """
    field_prefix = 'gcl'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('generator', 'categories'),
              StaticParam('prop', 'categoryinfo'),
              SingleParam('gclshow', '')]  # hidden, !hidden
    output_type = [CategoryInfo]
    examples = [OperationExample('Physics')]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                cat_info = CategoryInfo.from_query(pid_dict,
                                                   source=self.source)
            except ValueError:
                print ValueError
                continue
            if cat_info.page_id < 0:
                continue
            ret.append(cat_info)
        return ret


class GetCategory(QueryOperation):
    """
    Fetch the members in category.
    """
    field_prefix = 'gcm'
    input_field = SingleParam('title', val_prefix='Category:')
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection'),
              MultiParam('namespace')]
    output_type = [PageInfo]
    examples = [OperationExample('Featured_articles')]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                 source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetCategoryPages(GetCategory):
    """
    Fetch the pages (namespace 0 or 1) that are members of category.
    """
    fields = GetCategory.fields + [StaticParam('gcmnamespace', '0|1')]


class GetSubcategoryInfos(QueryOperation):
    """
    Fetch `CategoryInfo` for category, used to get the count of of members or
    sub-categories.
    """
    field_prefix = 'gcm'
    input_field = SingleParam('title', val_prefix='Category:')
    fields = [StaticParam('generator', 'categorymembers'),
              StaticParam('prop', 'categoryinfo'),
              StaticParam('gcmtype', 'subcat')]
    output_type = [CategoryInfo]
    examples = [OperationExample('FA-Class_articles')]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp['pages'].iteritems():
            try:
                pid_dict.update(pid_dict.get('categoryinfo', {}))
                cat_info = CategoryInfo.from_query(pid_dict,
                                                   source=self.source)
            except ValueError:
                continue
            if cat_info.page_id < 0:
                continue
            ret.append(cat_info)
        return ret


class GetAllCategoryInfos(GetSubcategoryInfos):
    """
    Fetch all categories on the source wiki.
    """
    field_prefix = 'gac'
    input_field = None
    fields = [StaticParam('generator', 'allcategories'),
              StaticParam('prop', 'categoryinfo')]
    examples = [OperationExample('basic allcats test')]


class GetFlattenedCategory(Operation):
    """
    Fetch all category's sub-categories.
    """
    subop_chain = [Tune(Recursive(GetSubcategoryInfos),
                        priority='subcat_count')]
    examples = [OperationExample('Africa', 100)]


class GetCategoryRecursive(Operation):
    """
    Fetch all the members of category and its sub-categories. A Wikipedia
    category tree can have a large number of shallow categories, so this
    operation will prioritize the larger categories by default.
    """
    subop_chain = (GetFlattenedCategory,
                   Tune(GetCategory, priority='total_count'))
    examples = [OperationExample('Africa', 100)]


class GetCategoryPagesRecursive(Operation):
    """
    Fetch all pages (namespace 0 and 1) in category and its sub-
    categories.
    """
    subop_chain = (GetFlattenedCategory,
                   Tune(GetCategoryPages, priority='page_count'))
    examples = [OperationExample('Africa', 100)]
