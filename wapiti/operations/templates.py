# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
import re

from base import QueryOperation
from params import SingleParam, StaticParam
from models import PageInfo


class GetTranscludes(QueryOperation):
    input_field = SingleParam('title', val_prefix='Template:')
    field_prefix = 'gei'
    fields = [StaticParam('generator', 'embeddedin'),
              StaticParam('prop', 'info'),
              StaticParam('inprop', 'subjectid|talkid|protection')]
    output_type = [PageInfo]

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
