# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import Operation, QueryOperation
from params import SingleParam, StaticParam
from models import RevisionInfo
from revisions import GetRevisionInfos
from utils import chunked_iter

DEFAULT_PROPS = 'ids|flags|timestamp|size|comment|tags|title'


class GetUserContribs(QueryOperation):
    field_prefix = 'uc'
    input_field = SingleParam('user')
    fields = [StaticParam('list', 'usercontribs'),
              StaticParam('ucprop', DEFAULT_PROPS)]
    output_type = [RevisionInfo]

    def extract_results(self, query_resp):
        ret = []
        for rev_dict in query_resp.get('usercontribs', []):
            try:
                user_contrib = RevisionInfo.from_query(rev_dict,
                                           source=self.source)
                ret.append(user_contrib)
            except ValueError:
                continue
        return ret


# TODO: fix
class GetUserContribRevisions(Operation):
    subop_chain = (GetUserContribs, GetRevisionInfos)
