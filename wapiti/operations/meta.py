# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation, MultiParam, StaticParam
from models import NamespaceDescriptor, InterwikiDescriptor


DEFAULT_PROPS = ('general',
                 'namespaces',
                 'namespacealiases',
                 'statistics',
                 'interwikimap')


class GetMeta(QueryOperation):
    '''
    http://en.wikipedia.org/w/api.php?action=query&meta=&siprop=&format=jsonfm
    http://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=general|namespaces|namespacealiases|statistics|interwikimap&format=jsonfm
    '''
    field_prefix = 'si'
    query_field = None
    fields = [StaticParam('meta', 'siteinfo'),
              MultiParam('prop', DEFAULT_PROPS)]

    def __init__(self, **kw):
        query_param = kw.pop('query_param', None)
        limit = kw.pop('limit', None)
        super(GetMeta, self).__init__(query_param, limit, **kw)

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
        return ret
