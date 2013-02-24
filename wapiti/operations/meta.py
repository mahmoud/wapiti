# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, SingleParam, StaticParam
from models import NamespaceDescriptor, InterwikiDescriptor


class GetMeta(QueryOperation):
    '''
    http://en.wikipedia.org/w/api.php?action=query
    &meta=&siprop=&format=jsonfm
    http://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=general|namespaces|namespacealiases|statistics|interwikimap&format=jsonfm
    '''
    field_prefix = 'si'
    query_field = False  # hmm
    fields = [StaticParam('meta', 'siteinfo'),
              StaticParam('siprop', 'general|namespaces|namespacealiases|statistics|interwikimap')]

    def __init__(self, **kw):
        super(GetMeta, self).__init__('Test', **kw)

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
        import pdb; pdb.set_trace()
        return ret
