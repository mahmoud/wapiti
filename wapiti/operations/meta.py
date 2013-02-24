# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, StaticParam
from collections import namedtuple


NamespaceDescriptor = namedtuple('NamespaceDescriptor', 'id title canonical')
InterwikiDescriptor = namedtuple('InterwikiDescriptor', 'prefix url language')


class GetMeta(QueryOperation):
    '''

    '''
    field_prefix = 'si'
    query_field = False  # hmm
    fields = [StaticParam('meta', 'siteinfo'),
              StaticParam('siprop', 'general|namespaces|namespacealiases|statistics|interwikimap')]

    def __init__(self, **kw):
        super(GetMeta, self).__init__('', **kw)

    def extract_results(self, query_resp):
        ret = query_resp['general']
        namespaces = query_resp.get('namespaces', {})
        interwikis = query_resp.get('interwikimap', {})
        ns_map = []
        for ns, ns_dict in namespaces.iteritems():
            ns_map.append(NamespaceDescriptor(ns_dict.get('id'),
                                              ns_dict.get('*'),
                                              ns_dict.get('canonical')))
        iw_map = []
        for iw in interwikis:
            iw_map.append(InterwikiDescriptor(iw.get('prefix'),
                                              iw.get('url'),
                                              iw.get('language')))
        ret['namespace_map'] = ns_map
        ret['interwiki_map'] = iw_map
        return [ret]
