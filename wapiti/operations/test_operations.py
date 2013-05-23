# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from argparse import ArgumentParser
from functools import wraps, partial
from pprint import pprint

import base
from models import PageIdentifier
from category import GetSubcategoryInfos

from revisions import GetCurrentContent, GetPageRevisionInfos, GetRevisionInfos

from misc import GetQueryPage
from meta import GetSourceInfo

import category
import feedback
import files
import links
import meta
import misc
import protection
import rand
import revisions
import templates
import user


def limit_equal_or_depleted(op):
    if getattr(op, '_notices', None):
        return False
    elif getattr(op, 'is_depleted', None):
        return True
    elif len(op.results) == op.limit:
        return True
    return False


def get_op_examples():
    ops = list(base.OperationMeta._all_ops)
    ret = []
    for op in ops:
        examples = getattr(op, 'examples', None)
        if not examples:
            continue
        ret.extend(op.examples)
    return ret


EXAMPLES = get_op_examples()
_TEST_TUPLES = [(ex.disp_name, ex) for ex in EXAMPLES]


@pytest.mark.parametrize(('name', 'op_ex'), _TEST_TUPLES)
def test_op_example(name, op_ex, limit=None):
    try:
        limit = int(limit)
    except:
        limit = 1
    op = op_ex.make_op(mag=limit)
    op.process_all()
    if callable(op_ex.test):
        assert op_ex.test(op)
    else:
        assert limit_equal_or_depleted(op)


def test_unicode_title():
    get_beyonce = GetCurrentContent("Beyoncé Knowles")
    assert get_beyonce()


def test_coercion_basic():
    pid = PageIdentifier(title='Africa', page_id=123, ns=4, source='enwp')
    get_subcats = GetSubcategoryInfos(pid)
    assert get_subcats.input_param == 'Category:Africa'


def test_web_request():
    url = 'http://upload.wikimedia.org/wikipedia/commons/d/d2/Mcgregor.jpg'
    get_photo = base.WebRequestOperation(url)
    res = get_photo()
    text = res[0]
    assert len(text) == 16408


def test_get_html():
    get_africa_html = base.GetPageHTML('Africa')
    res = get_africa_html()
    text = res[0]
    assert len(text) > 350000


def test_missing_revisions():
    get_revs = GetPageRevisionInfos('Coffee_lololololol')
    rev_list = get_revs()
    '''
    Should return 'missing' and negative pageid
    '''
    assert len(rev_list) == 0


def test_multiplexing(limit=5):
    rev_ids = [str(x) for x in range(543184935 - limit, 543184935)]
    get_rev_infos = GetRevisionInfos(rev_ids)
    rev_infos = get_rev_infos()
    assert len(rev_infos) > (0.9 * limit)  # a couple might be missing


def test_query_pages(limit=3):
    qp_types = GetQueryPage.known_qps[:limit]
    ret = []
    for qpt in qp_types:
        get_pages = GetQueryPage(qpt, limit)
        ret.extend(get_pages())
    assert len(ret) == len(qp_types)


def test_get_meta():
    get_source_info = GetSourceInfo()
    meta = get_source_info()
    assert meta
