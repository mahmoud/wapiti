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

#def operation_example(request):
#    return request.param


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
