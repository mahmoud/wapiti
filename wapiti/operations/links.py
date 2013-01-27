# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import PageIdentifier, QueryOperation
from collections import namedtuple

LanguageLink = namedtuple('LanguageLink', 'url language origin_page')
InterwikiLink = namedtuple('InterwikiLink', 'url prefix origin_page')


class GetBacklinks(QueryOperation):
    param_prefix = 'bl'
    query_param_name = param_prefix + 'title'
    static_params = {'list': 'backlinks'}

    def extract_results(self, query_resp):
        ret = []
        for link in query_resp.get('backlinks', []):
            page_id = link.get('pageid')
            if not page_id:
                continue
            ns = link['ns']
            title = link['title']
            ret.append(PageIdentifier(title=title,
                                      page_id=page_id,
                                      ns=ns,
                                      source=self.source))
        return ret


class GetLanguageLinks(QueryOperation):
    param_prefix = 'll'
    query_param_name = 'titles'
    static_params = {'prop': 'langlinks',
                     'llurl': 'true'}

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            page_id = pid_dict['pageid']
            ns = pid_dict['ns']
            title = pid_dict['title']
            page_ident = PageIdentifier(title=title,
                                        page_id=page_id,
                                        ns=ns,
                                        source=self.source)
            for ld in pid_dict.get('langlinks', []):
                link = LanguageLink(ld.get('url'),
                                    ld.get('lang'),
                                    page_ident)
                ret.append(link)
        return ret


class GetInterwikiLinks(QueryOperation):
    param_prefix = 'iw'
    query_param_name = 'titles'
    static_params = {'prop': 'iwlinks',
                     'iwurl': 'true'}

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            page_id = pid_dict['pageid']
            ns = pid_dict['ns']
            title = pid_dict['title']
            page_ident = PageIdentifier(title=title,
                                        page_id=page_id,
                                        ns=ns,
                                        source=self.source)
            for iwd in pid_dict.get('iwlinks', []):
                link = InterwikiLink(iwd.get('url'),
                                     iwd.get('prefix'),
                                     page_ident)
                ret.append(link)
        return ret
