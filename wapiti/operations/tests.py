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


#def operation_example(request):
#    return request.param


@pytest.mark.parametrize(('name', 'opex'), [(repr(ex), ex) for ex in EXAMPLES])
def test_op_example(name, opex, limit=None):
    try:
        limit = int(limit)
    except:
        limit = 1
    op = opex.make_op(mag=limit)
    op.process_all()
    assert opex.test(op)
