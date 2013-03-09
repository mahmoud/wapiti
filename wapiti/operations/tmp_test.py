# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from argparse import ArgumentParser
from pprint import pprint

from category import GetSubcategoryInfos, GetCategory, GetCategoryRecursive

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


def test_subcategory_infos(limit=20):
    get_subcats = GetSubcategoryInfos('FA-Class_articles', limit)
    subcats = call_and_ret(get_subcats)
    return len(subcats) == limit


def test_category_basic(limit=20):
    get_2k_featured = GetCategory('Featured_articles', limit)
    pages = call_and_ret(get_2k_featured)
    return len(pages) == limit


def test_category_recursive(limit):
    get_limit_recursive = GetCategoryRecursive('Africa', limit)
    pages = call_and_ret(get_limit_recursive)
    return len(pages) == limit


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
