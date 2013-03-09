# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from argparse import ArgumentParser
from pprint import pprint

from category import GetSubcategoryInfos
from models import PageIdentifier

PDB_ALL = True
PDB_ERROR = False
DO_PRINT = False
DEFAULT_MAGNITUDE = 20


def call_and_ret(func):
    try:
        ret = func()
    except Exception as e:
        if PDB_ERROR:
            import pdb;pdb.post_mortem()
        raise
    if PDB_ALL:
        import pdb;pdb.set_trace()
    if ret:
        try:
            disp = ret[0]
        except TypeError:
            disp = ret
        print repr(disp)[:74] + '...'
    return ret


def test_coercion_basic(limit=20):
    get_subcats = GetSubcategoryInfos(PageIdentifier(title='Africa',
                                                     page_id=123,
                                                     ns=4,
                                                     source='enwp'), limit)

    return get_subcats.input_param == 'Category:Africa'


def create_parser():
    parser = ArgumentParser(description='Test operations')
    parser.add_argument('functions', nargs='*')
    parser.add_argument('--pdb_all', '-a', action='store_true')
    parser.add_argument('--pdb_error', '-e', action='store_true')
    parser.add_argument('--do_print', '-p', action='store_true')
    parser.add_argument('--magnitude', '-m',
                        default=DEFAULT_MAGNITUDE)
    return parser


def main():
    global PDB_ALL, PDB_ERROR, DO_PRINT
    parser = create_parser()
    args = parser.parse_args()
    PDB_ALL = args.pdb_all
    PDB_ERROR = args.pdb_error
    DO_PRINT = args.do_print
    if args.functions:
        tests = {}
        for func in args.functions:
            try:
                tests[func] = globals()[func]
            except KeyError:
                print func, 'is not a valid test function'
                continue
    else:
        tests = dict([(k, v) for k, v in globals().items()
                      if callable(v) and k.startswith('test_')])
    results = {}
    for k, v in tests.items():
        results[k] = v(args.magnitude)
        print k, results[k]
    return results


if __name__ == '__main__':
    pprint(main())
