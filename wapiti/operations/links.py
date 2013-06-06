# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from params import SingleParam, MultiParam, StaticParam
from models import (PageInfo, LanguageLink, InterwikiLink, ExternalLink)
from utils import OperationExample


class GetBacklinks(QueryOperation):
    """
    Fetch page's incoming links from other pages on source wiki.
    """
    field_prefix = 'gbl'
    input_field = SingleParam('title')
    fields = [StaticParam('generator', 'backlinks'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    output_type = [PageInfo]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid, pid_dict in query_resp.get('pages', {}).iteritems():
            page_info = PageInfo.from_query(pid_dict,
                                            source=self.source)
            ret.append(page_info)
        return ret


class GetLinks(QueryOperation):
    """
    Fetch page's outgoing links to other pages on source wiki.
    """
    field_prefix = 'gpl'
    input_field = SingleParam('titles', key_prefix=False)
    fields = [StaticParam('generator', 'links'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection'),
              MultiParam('namespace')]
    output_type = [PageInfo]
    examples = [OperationExample('Coffee'),
                OperationExample('Aabach')]

    def extract_results(self, query_resp):
        ret = []
        for pid, pid_dict in query_resp['pages'].iteritems():
            try:
                page_info = PageInfo.from_query(pid_dict,
                                                source=self.source)
            except ValueError:
                # TODO: red links have no page ID, maybe add a flag to
                # include red links instead of skipping them? Or maybe
                # a separate operation to get only red links. How
                # often do folks want both instead of one or the
                # other?
                continue
            ret.append(page_info)
        return ret


class GetExternalLinks(QueryOperation):
    """
    Fetch page outgoing links to URLs outside of source wiki.
    """
    field_prefix = 'el'
    input_field = SingleParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'extlinks')]
    output_type = [ExternalLink]
    examples = [OperationExample('Croatian War of Independence')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            for el in pid_dict.get('extlinks', []):
                cur_dict = dict(pid_dict)
                cur_dict['source'] = self.source
                cur_dict['url'] = el.get('*')
                link = ExternalLink.from_query(cur_dict)
                ret.append(link)
        return ret

    def prepare_params(self, **kw):
        params = super(GetExternalLinks, self).prepare_params(**kw)
        if params.get('elcontinue'):
            params['eloffset'] = params.pop('elcontinue')
        return params


class GetLanguageLinks(QueryOperation):
    """
    Fetch pages' interlanguage links (aka "Language Links" in the MediaWiki
    API). Interlanguage links should correspond to pages on another language
    wiki. Mostly useful on a source wiki with a family of similar multilingual
    projects, such as Wikipedias.
    """
    field_prefix = 'll'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'langlinks'),
              SingleParam('url', True)]
    output_type = [LanguageLink]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            for ld in pid_dict.get('langlinks', []):
                cur_dict = dict(pid_dict)
                cur_dict['source'] = self.source
                cur_dict['url'] = ld.get('*')
                cur_dict['language'] = ld.get('lang')
                link = LanguageLink.from_query(cur_dict)
                ret.append(link)
        return ret


class GetInterwikiLinks(QueryOperation):
    """
    Fetch pages' interwiki links.
    """
    field_prefix = 'iw'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('prop', 'iwlinks'),
              SingleParam('url', True)]
    output_type = [InterwikiLink]
    examples = [OperationExample('Coffee')]

    def extract_results(self, query_resp):
        ret = []
        for pid_dict in query_resp.get('pages', {}).values():
            for iwd in pid_dict.get('iwlinks', []):
                cur_dict = dict(pid_dict)
                cur_dict['source'] = self.source
                cur_dict['url'] = iwd.get('url')
                cur_dict['prefix'] = iwd.get('prefix')
                link = InterwikiLink.from_query(cur_dict)
                ret.append(link)
        return ret
