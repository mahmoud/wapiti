# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base import Operation, QueryOperation
from params import SingleParam, StaticParam
from models import PageIdentifier, UserContrib
from revisions import GetRevisionInfos

DEFAULT_PROPS = 'ids|flags|timestamp|user|userid|size|sha1|comment|tags|title'


class GetUserContribs(QueryOperation):
    field_prefix = 'uc'
    input_field = SingleParam('user', required=True)
    fields = [StaticParam('list', 'usercontribs'),
              StaticParam('ucprop', DEFAULT_PROPS)]
    output_type = [PageIdentifier]

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


def chunked_iter(src, size, **kw):
    """
    Generates 'size'-sized chunks from 'src' iterable. Unless
    the optional 'fill' keyword argument is provided, iterables
    not even divisible by 'size' will have a final chunk that is
    smaller than 'size'.

    Note that fill=None will in fact use None as the fill value.

    >>> list(chunked_iter(range(10), 3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    >>> list(chunked_iter(range(10), 3, fill=None))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]
    """
    size = int(size)
    if size <= 0:
        raise ValueError('expected a positive integer chunk size')
    do_fill = True
    try:
        fill_val = kw.pop('fill')
    except KeyError:
        do_fill = False
        fill_val = None
    if kw:
        raise ValueError('got unexpected keyword arguments: %r' % kw.keys())
    if not src:
        return
    cur_chunk = []
    i = 0
    for item in src:
        cur_chunk.append(item)
        i += 1
        if i % size == 0:
            yield cur_chunk
            cur_chunk = []
    if cur_chunk:
        if do_fill:
            lc = len(cur_chunk)
            cur_chunk[lc:] = [fill_val] * (size - lc)
        yield cur_chunk
    return
