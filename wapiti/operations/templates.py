# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
import re

from base import QueryOperation, Operation, NoMoreResults
from params import SingleParam, StaticParam, MultiParam, PassthroughParam
from models import PageInfo
from utils import OperationExample
from revisions import GetCurrentContent
from template_parser import get_page_templates, TemplateReference, _BASIC_CITE_TEST


class GetTemplates(QueryOperation):
    field_prefix = 'gtl'
    input_field = MultiParam('titles', key_prefix=False)
    fields = [StaticParam('generator', 'templates'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    output_type = [PageInfo]
    examples = [OperationExample('Coffee')]

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


class GetTranscludes(QueryOperation):
    input_field = SingleParam('title', val_prefix='Template:')
    field_prefix = 'gei'
    fields = [StaticParam('generator', 'embeddedin'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    output_type = [PageInfo]
    examples = [OperationExample('Template:ArticleHistory')]

    def extract_results(self, query_resp):
        ret = []
        for k, pid_dict in query_resp.get('pages', {}).items():
            try:
                page_ident = PageInfo.from_query(pid_dict,
                                                 source=self.source)
            except ValueError:
                continue
            ret.append(page_ident)
        return ret


class GetParsedTemplates(Operation):
    input_field = PassthroughParam('content')
    output_type = [TemplateReference]
    examples = [OperationExample(_BASIC_CITE_TEST, limit=1)]

    @property
    def remaining(self):
        if self.results:
            return 0
        return 1  # TODO: fix

    def process(self):
        if None in self.results:
            raise NoMoreResults()
        content = getattr(self.input_param, 'content', self.input_param)
        res = get_page_templates(content, raise_exc=False)
        self.results[None] = res
        return list(res)


class GetParsedTranscludes(Operation):
    '''
    Template names may redirect, but this operation doesn't handle that yet
    '''
    subop_chain = [GetTranscludes,
                   GetCurrentContent,
                   GetParsedTemplates]
    examples = [OperationExample('ArticleHistory', 10)]

    def _update_results(self, results):
        _, _, tmpl_name = self.input_param.rpartition(':')
        filt_res = [res for res in results
                    if res.name.lower() == tmpl_name.lower()]
        return super(GetParsedTranscludes, self)._update_results(filt_res)


def tmpl_text_to_odict(text):
    ret = OrderedDict()
    pairs = text.split('|')
    for p in pairs:
        p = p.strip()
        if not p:
            continue
        k, _, v = p.partition('=')
        k = k.strip()
        v = v.strip()
        if not k:
            print 'blank key error', k
            #import pdb;pdb.set_trace()
            continue
        if k in ret:
            print 'duplicate key error', k
            #import pdb;pdb.set_trace()
            continue
        ret[k] = v
    return ret


def extract_template(tmpl_name, text):
    ret = []
    tmpl_re = re.compile('\{\{(\s*' + tmpl_name + '.*?)\}\}',
                         flags=(re.DOTALL | re.IGNORECASE| re.M))
    tmpl_txts = re.findall(tmpl_re, text)
    for txt in tmpl_txts:
        ret.append(tmpl_text_to_odict(txt))
    return ret


#class GetAllTranscludes(GetTranscludes):
#    field_prefix = 'at'
#    input_field = None
#    fields = [StaticParam('list', 'alltransclusions'),
#              #StaticParam('prop', 'info'),
#              StaticParam('atprop', 'ids|title')] # 'subjectid|talkid|protection')]
