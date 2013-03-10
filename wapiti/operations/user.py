# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import Operation, QueryOperation
from params import SingleParam, StaticParam
from models import PageIdentifier, UserContrib
from revisions import GetRevisionInfos
from utils import chunked_iter

DEFAULT_PROPS = 'ids|flags|timestamp|size|comment|tags|title'


class GetUserContribs(QueryOperation):
    field_prefix = 'uc'
    input_field = SingleParam('user')
    fields = [StaticParam('list', 'usercontribs'),
              StaticParam('ucprop', DEFAULT_PROPS)]
    output_type = [UserContrib]

    def extract_results(self, query_resp):
        ret = []
        for rev_dict in query_resp.get('usercontribs', []):
            try:
                page_ident = PageIdentifier.from_query(rev_dict,
                                                       source=self.source)
                user_contrib = UserContrib(page_ident,
                                           rev_dict['user'],
                                           rev_dict['userid'],
                                           rev_dict['revid'])
                ret.append(user_contrib)
            except ValueError:
                continue
        return ret


# TODO: fix
class GetUserContribRevisionInfos(Operation):
    subop_chain = (GetUserContribs, GetRevisionInfos)

    def __produce_suboperations(self):
        if not self.generator or not self.generator.remaining:
            return None
        ret = []
        generated = self.generator.process()
        for res_group in chunked_iter(generated, 50):
            id_group = [r.revision_id for r in res_group]
            get_rev_infos = GetRevisionInfos(id_group)
            self.suboperations.add(get_rev_infos, 0)
            ret.append(get_rev_infos)
        return ret
