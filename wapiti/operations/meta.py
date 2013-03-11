# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import QueryOperation
from params import MultiParam, StaticParam
from models import NamespaceDescriptor, InterwikiDescriptor, SourceInfo


DEFAULT_PROPS = ('general',
                 'namespaces',
                 'namespacealiases',
                 'statistics',
                 'interwikimap')
"""
OTHER_PROPS = ['namespaces',
               'namespacealiases',
               'specialpagealiases',
               'magicwords',
               'statistics',
               'interwikimap',
               'dbrepllag',
               'usergroups',
               'extensions',
               'fileextensions',
               'rightsinfo',
               'languages',
               'skins',
               'extensiontags',
               'functionhooks',
               'showhooks',
               'variables',
               'protocols']
 """


class GetSourceInfo(QueryOperation):
    """
    Fetch meta site information about the source wiki.

    The default properties include:

    - General source information: Main Page, base, sitename, generator,
      phpversion,  phpsapi, dbtype, dbversion, case, rights, lang, fallback,
      fallback8bitEncoding, writeapi, timezone, timeoffset, articlepath,
      scriptpath, script, variantarticlepath, server, wikiid, time, misermode,
      maxuploadsize
    - Namespace map
    - Interwiki map
    - Statistics: pages, articles, edits, images, users, activeusers, admins,
      jobs
    """
    field_prefix = 'si'
    input_field = None
    fields = [StaticParam('meta', 'siteinfo'),
              MultiParam('prop', DEFAULT_PROPS)]
    output_type = SourceInfo

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
        ret['namespace_map'] = tuple(ns_map)
        ret['interwiki_map'] = tuple(iw_map)
        ret.update(query_resp['statistics'])
        source_info = SourceInfo(**ret)
        return [source_info]
