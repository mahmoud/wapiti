# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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


PDB_ALL = True
PDB_ERROR = False
DO_PRINT = False

DEFAULT_MAGNITUDE = 'norm'

# magnitude levels: norm (fetch a small number)
#                   big (fetch a enough to hit the continue string)
#                   huge (fetch a huge amount)
#   Note: pages may not contain enough items to pass big/huge tests


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


def magnitude(norm, big=None, huge=None):
    if big is None:
        big = norm
    if huge is None:
        huge = big

    def mag_dec(func):
        @wraps(func)
        def wrapped(limit_or_mag=None):
            if limit_or_mag is None:
                limit_or_mag = wrapped.norm
            try:
                limit = int(limit_or_mag)
            except ValueError:
                limit = int(wrapped.__dict__[limit_or_mag])
            return func(limit)
        wrapped.norm = norm
        wrapped.big = big
        wrapped.huge = huge
        return wrapped
    return mag_dec


def get_tests():
    tests = dict([(k, v) for k, v in globals().items()
                  if callable(v) and k.startswith('test_')])
    return tests


def get_operations():
    return list(base.OperationMeta._all_ops)
    #return [obj for obj in globals().values()
    #        if isinstance(obj, type)
    #        and issubclass(obj, base.Operation)]


def get_op_examples():
    ops = get_operations()
    ret = []
    for op in ops:
        examples = getattr(op, 'examples', None)
        if not examples:
            continue
        ret.extend(op.examples)
    return ret


def op_example(operation, limit=None):
    try:
        limit = int(limit)
    except:
        limit = 1
    ret = {}
    ops = get_operations()
    for op in (o for o in ops if o.__name__ == operation):
        example = getattr(op, 'examples', None)
        for ex in example:
            op = ex.make_op(mag=limit)
            op.process_all()
            ret[ex.disp_name] = ex.test(op)
    return all(ret.values())


def test_example_operations(limit=None):
    try:
        limit = int(limit)
    except:
        limit = 1
    ex_ops = get_op_examples()
    results = {}
    for ex in ex_ops:
        op = ex.make_op(mag=limit)
        op.process_all()
        results[ex.disp_name] = ex.test(op)
    return all(results.values())


def test_unicode_title(limit):
    get_beyonce = GetCurrentContent("Beyoncé Knowles")
    beyonce = call_and_ret(get_beyonce)
    return bool(beyonce)


def test_coercion_basic(limit=None):
    pid = PageIdentifier(title='Africa', page_id=123, ns=4, source='enwp')
    get_subcats = GetSubcategoryInfos(pid, limit)
    return get_subcats.input_param == 'Category:Africa'


@magnitude(norm=100, big=1000, huge=2200)
def test_multiplexing(limit=None):
    rev_ids = [str(x) for x in range(543184935 - limit, 543184935)]
    get_rev_infos = GetRevisionInfos(rev_ids)
    rev_infos = call_and_ret(get_rev_infos)
    return len(rev_infos) > (0.9 * limit)  # a couple might be missing


def test_web_request(limit=None):
    url = 'http://upload.wikimedia.org/wikipedia/commons/d/d2/Mcgregor.jpg'
    get_photo = base.WebRequestOperation(url)
    res = get_photo()
    text = res[0]
    return len(text) == 16408


def test_get_html(limit=None):
    get_africa_html = base.GetPageHTML('Africa')
    res = get_africa_html()
    text = res[0]
    return len(text) > 350000


def test_nonexistent_cat_error(limit):
    '''
    Should return invalidcategory error
    {"servedby":"mw1204","error":{"code":"gcminvalidcategory","info":"The category name you entered is not valid"}}
    ```
    nonexistent_cat = GetCategory('DoesNotExist', 100)
    pages = call_and_ret(nonexistent_cat)
    '''
    pass


def test_nonexistent_prot(limit):
    '''
    returns 'missing' and negative id
    get_nonexistent_prot = GetProtections('DoesNotExist')
    prots = call_and_ret(get_nonexistent_prot)
    '''
    pass


def test_nonexistent_lang_links(limit):
    '''
    returns 'missing' and negative id
    get_nonexistent_ll = GetLanguageLinks('DoesNotExist')
    lang_list = call_and_ret(get_nonexistent_ll)
    '''
    pass


def test_nonexistent_iw_links(limit):
    '''
    returns 'missing' and negative id
    get_nonexistent_iwl = GetInterwikiLinks('DoesNotExist')
    iw_list = call_and_ret(get_nonexistent_iwl)
    '''
    pass


def test_missing_revisions(limit):
    get_revs = GetPageRevisionInfos('Coffee_lololololol')
    rev_list = call_and_ret(get_revs)
    '''
    Should return 'missing' and negative pageid
    '''
    return len(rev_list) == 0


'''
def test_get_meta(limit):
    get_source_info = GetSourceInfo()
    meta = call_and_ret(get_source_info)
    return bool(meta)
'''


@magnitude(norm=2, big=5, huge=600)
def test_query_pages(limit):
    qp_types = GetQueryPage.known_qps[:limit]
    ret = []
    for qpt in qp_types:
        get_pages = GetQueryPage(qpt, limit)
        ret.extend(call_and_ret(get_pages))
    return len(ret) == len(qp_types)


def test_nonexistent_query_page(limit):
    try:
        non_existent_qp = GetQueryPage('FakeQueryPage')
        call_and_ret(non_existent_qp)
    except ValueError:
        return True


def create_parser():
    parser = ArgumentParser(description='Test operations')
    parser.add_argument('targets', nargs='*')
    parser.add_argument('--list', '-l', action='store_true')
    parser.add_argument('--pdb_all', '-a', action='store_true')
    parser.add_argument('--no_pdb_int', action='store_true')
    parser.add_argument('--no_pdb_error', '-e', action='store_true')
    parser.add_argument('--do_print', '-p', action='store_true')
    parser.add_argument('--magnitude', '-m',
                        default=DEFAULT_MAGNITUDE)
    return parser


def _install_int_handler():
    import signal, pdb
    def pdb_int_handler(sig, frame):
        pdb.set_trace()
    signal.signal(signal.SIGINT, pdb_int_handler)


def main():
    global PDB_ALL, PDB_ERROR, DO_PRINT
    parser = create_parser()
    args = parser.parse_args()
    PDB_ALL = args.pdb_all
    PDB_ERROR = not args.no_pdb_error
    print PDB_ERROR
    DO_PRINT = args.do_print

    if not args.no_pdb_int:
        _install_int_handler()
    all_tests = get_tests()
    possible_ops = [op.__name__ for op in get_operations()
                    if getattr(op, 'examples', None)]
    possible_ops += all_tests.keys()

    if args.targets:
        tests = {}
        for func in args.targets:
            try:
                if func in all_tests.keys():
                    tests[func] = globals()[func]
                else:
                    tests[func] = partial(op_example, func)
            except KeyError:
                print func, 'is not a valid test function'
                continue
    else:
        tests = all_tests
    if args.list:
        print 'Available tests:'
        pprint(possible_ops)
        return
    results = {}
    for test_name, test in tests.items():
        magged_test_func = partial(test, args.magnitude)
        results[test_name] = call_and_ret(magged_test_func)
        print test_name, results[test_name]
    if not results:
        print '-- no tests run'
        return
    pprint(results)
    print
    failures = [k for k, v in results.items() if not v and v is not None]
    if failures:
        print '-- the following tests failed: %r' % failures
    else:
        print '++ all tests passed'
    print

    return results

if __name__ == '__main__':
    main()
