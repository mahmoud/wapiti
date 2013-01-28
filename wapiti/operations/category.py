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
                page_ident = PageIdentifier.from_query_result(pid_dict,
                                                              self.source)
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
        for k, cm in query_resp['pages'].iteritems():
            if not cm.get('pageid') or k < 0:
                continue
            namespace = cm['ns']
            title = cm['title']
            page_id = cm['pageid']
            ci = cm.get('categoryinfo')
            if ci:
                size = ci['size']
                pages = ci['pages']
                files = ci['files']
                subcats = ci['subcats']
            else:
                size, pages, files, subcats = (0, 0, 0, 0)
            ret.append(CategoryInfo(title=title,
                                    page_id=page_id,
                                    ns=namespace,
                                    source=self.source,
                                    total_count=size,
                                    page_count=pages,
                                    file_count=files,
                                    subcat_count=subcats))
        return ret
