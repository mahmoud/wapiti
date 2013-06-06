# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base
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

from revisions import GetRevisionInfos

MAGNITUDE = 1


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


def pytest_generate_tests(metafunc):
    #if 'limit' in metafunc.fixturenames:  # TODO
    # keyword = metafunc.config.option.keyword
    # it's also too hard to override matching behavior
    if metafunc.function is test_op_example:
        mag = metafunc.config.getoption('--mag')
        op_examples = get_op_examples()
        #op_examples = [ex for ex in op_examples
        #               if keyword.lower() in ex.op_name.lower()]
        ops = [op_ex.make_op(mag=mag) for op_ex in op_examples]
        _test_tuples = [(repr(op), op) for op in ops]
        metafunc.parametrize(('op_repr', 'op'), _test_tuples)
        pass


#def pytest_funcarg__mag(request):
#    # TODO: switch to command line argument
#    return MAGNITUDE


#def pytest_funcarg__limit(request):
# wish there was a good way to compose this with mag and the current
# value of the function's "limit" keyword argument to make the final
# limit return 1


def test_multiplexing(mag):
    limit = mag * 100
    rev_ids = [str(x) for x in range(543184935 - limit, 543184935)]
    get_rev_infos = GetRevisionInfos(rev_ids)
    rev_infos = get_rev_infos()
    assert len(rev_infos) > (0.9 * limit)  # a couple might be missing


def test_op_example(op_repr, op):
    op.process_all()
    assert limit_equal_or_depleted(op)
