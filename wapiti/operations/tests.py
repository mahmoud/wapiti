# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from argparse import ArgumentParser
from functools import wraps
from pprint import pprint

import base
from category import (GetCategory,
                      GetCategoryList,
                      GetSubcategoryInfos,
                      GetFlattenedCategory,
                      GetCategoryRecursive,
                      GetCategoryPagesRecursive,
                      GetAllCategoryInfos)
from rand import GetRandom
from protection import GetProtections
from links import (GetBacklinks,
                   GetLanguageLinks,
                   GetInterwikiLinks,
                   GetExternalLinks,
                   GetImages,
                   GetLinks)
from feedback import GetFeedbackV5
from revisions import (GetPageRevisionInfos,
                       GetRevisionInfos,
                       GetCurrentContent,
                       GetCurrentTalkContent)
from templates import GetTranscludes, GetAllTranscludes
from misc import (GetCoordinates,
                  GeoSearch,
                  GetImageInfos,
                  GetTemplates,
                  GetQueryPage,
                  GetRecentChanges,
                  GetAllImageInfos)
from user import (GetUserContribs,
                  GetUserContribRevisionInfos)
from meta import GetSourceInfo

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


def test_unicode_title(limit):
    get_beyonce = GetCurrentContent("Beyoncé Knowles")
    beyonce = call_and_ret(get_beyonce)
    return bool(beyonce)


@magnitude(norm=20, big=550, huge=2000)
def test_category_basic(limit):
    get_2k_featured = GetCategory('Featured_articles', limit)
    pages = call_and_ret(get_2k_featured)
    return len(pages) == limit


def test_nonexistent_cat_error(limit):
    '''
    Should return invalidcategory error
    {"servedby":"mw1204","error":{"code":"gcminvalidcategory","info":"The category name you entered is not valid"}}
    ```
    nonexistent_cat = GetCategory('DoesNotExist', 100)
    pages = call_and_ret(nonexistent_cat)
    '''
    pass


def test_multiplexing(limit=None):
    rev_ids = [str(x) for x in range(543184935 - 100, 543184935)]
    get_rev_infos = GetRevisionInfos(rev_ids)
    rev_infos = call_and_ret(get_rev_infos)
    return len(rev_infos) > 90  # a couple might be missing


@magnitude(norm=20, big=550, huge=2000)
def test_subcategory_infos(limit):
    get_subcats = GetSubcategoryInfos('FA-Class_articles', limit)
    subcats = call_and_ret(get_subcats)
    return len(subcats) == limit


def test_all_category_infos(limit):
    get_all_cats = GetAllCategoryInfos(501)
    all_cats = call_and_ret(get_all_cats)
    return len(all_cats) == 501


@magnitude(norm=10, big=1000, huge=10000)
def test_category_recursive(limit):
    get_limit_recursive = GetCategoryRecursive('Africa', limit)
    pages = call_and_ret(get_limit_recursive)
    return len(pages) == limit


def test_single_prot(limit):
    get_coffee_prot = GetProtections('Coffee')
    prots = call_and_ret(get_coffee_prot)
    return len(prots) == 1


def test_multi_prots_list(limit):
    get_prots = GetProtections(['Coffee', 'House'])
    prots = call_and_ret(get_prots)
    return len(prots) == 2


def test_multi_prots_str(limit):
    get_prots = GetProtections('Coffee|House')
    prots = call_and_ret(get_prots)
    return len(prots) == 2


def test_nonexistent_prot(limit):
    '''
    returns 'missing' and negative id
    get_nonexistent_prot = GetProtections('DoesNotExist')
    prots = call_and_ret(get_nonexistent_prot)
    '''
    pass


@magnitude(norm=20, big=550, huge=2000)
def test_backlinks(limit):
    get_bls = GetBacklinks('Coffee', limit)
    bls = call_and_ret(get_bls)
    '''
    Nonexistent title returns []
    '''
    return len(bls) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_random(limit):
    get_fifty_random = GetRandom(limit)
    pages = call_and_ret(get_fifty_random)
    return len(pages) == limit


@magnitude(norm=5, big=550, huge=2000)
def test_lang_links(limit):
    get_coffee_langs = GetLanguageLinks('Coffee', limit)
    lang_list = call_and_ret(get_coffee_langs)
    return len(lang_list) == limit


def test_nonexistent_lang_links(limit):
    '''
    returns 'missing' and negative id
    get_nonexistent_ll = GetLanguageLinks('DoesNotExist')
    lang_list = call_and_ret(get_nonexistent_ll)
    '''
    pass


@magnitude(norm=5, big=550, huge=2000)
def test_interwiki_links(limit):
    get_coffee_iwlinks = GetInterwikiLinks('Coffee', limit)
    iw_list = call_and_ret(get_coffee_iwlinks)
    return len(iw_list) == limit


def test_nonexistent_iw_links(limit):
    '''
    returns 'missing' and negative id
    get_nonexistent_iwl = GetInterwikiLinks('DoesNotExist')
    iw_list = call_and_ret(get_nonexistent_iwl)
    '''
    pass


@magnitude(norm=20, big=550, huge=2000)
def test_external_links(limit):
    get_coffee_elinks = GetExternalLinks('Croatian War of Independence', limit)
    el_list = call_and_ret(get_coffee_elinks)
    assert len(set(el_list)) == len(el_list)
    return len(el_list) == limit


#def test_feedback_v4(limit):  # no longer available, see feedback.py for info
#    get_v4 = GetFeedbackV4('604727')
#    v4_list = call_and_ret(get_v4)
#    return len(v4_list) > 1


def test_feedback_v5(limit):
    get_v5 = GetFeedbackV5('604727')  # TODO: support ints
    v5_list = call_and_ret(get_v5)
    return isinstance(v5_list, list)


@magnitude(norm=10, big=550, huge=2000)
def test_revisions(limit):
    get_revs = GetPageRevisionInfos('Coffee', 10)
    rev_list = call_and_ret(get_revs)
    return len(rev_list) == 10


def test_missing_revisions(limit):
    get_revs = GetPageRevisionInfos('Coffee_lololololol')
    rev_list = call_and_ret(get_revs)
    '''
    Should return 'missing' and negative pageid
    '''
    return len(rev_list) == 0


@magnitude(norm=20, big=550, huge=2000)
def test_transclusions(limit):
    get_transcludes = GetTranscludes('Template:ArticleHistory', limit)
    tr_list = call_and_ret(get_transcludes)
    '''
    Nonexistent title returns []
    '''
    return len(tr_list) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_all_transcludes(limit):
    get_all_transcludes = GetAllTranscludes(limit)
    tr_list = call_and_ret(get_all_transcludes)
    return len(tr_list) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_resolve_subjects(limit):
    get_res_transcludes = GetTranscludes('Template:ArticleHistory', limit)
    pages = call_and_ret(get_res_transcludes)
    return len(pages) == limit


@magnitude(norm=11, big=550, huge=2000)
def test_cat_list(limit):
    get_cat_list = GetCategoryList('Physics', limit)
    pages = call_and_ret(get_cat_list)
    return len(pages) == limit


@magnitude(norm=4, big=550, huge=2000)
def test_get_images(limit):
    get_imgs = GetImages('Coffee', limit)
    imgs = call_and_ret(get_imgs)
    return len(imgs) == limit or get_imgs.last_cont_str is None


@magnitude(norm=5, big=550, huge=2000)
def test_get_links(limit):
    get_links = GetLinks('Coffee', limit)
    links = call_and_ret(get_links)
    return len(links) == limit


def test_coordinates(limit):
    get_coordinates = GetCoordinates(['White House', 'Golden Gate Bridge', 'Mount Everest'])
    coords = call_and_ret(get_coordinates)
    return len(coords) == 3


def test_geosearch(limit):
    geosearch = GeoSearch(('37.8197', '-122.479'))
    geo = call_and_ret(geosearch)
    return len(geo) > 1


@magnitude(norm=20, big=550, huge=2000)
def test_get_user_contribs(limit):
    get_contribs = GetUserContribs('Jimbo Wales', limit)
    contribs = call_and_ret(get_contribs)
    return len(contribs) == limit


def test_get_meta(limit):
    get_source_info = GetSourceInfo()
    meta = call_and_ret(get_source_info)
    return bool(meta)


def test_get_revision_infos(limit):
    get_revisions = GetRevisionInfos(['538903663', '539916351', '531458383'])
    rev_infos = call_and_ret(get_revisions)
    return len(rev_infos) == 3


def test_get_image_info(limit):
    get_image_info = GetImageInfos('File:Logo.gif')
    image_info = call_and_ret(get_image_info)
    return image_info[0].url == 'http://upload.wikimedia.org/wikipedia/en/e/ea/Logo.gif'


@magnitude(norm=20, big=550, huge=2000)
def test_get_all_image_infos(limit):
    get_all_img = GetAllImageInfos(limit)
    all_imgs = call_and_ret(get_all_img)
    return len(all_imgs) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_get_templates(limit):
    get_templates = GetTemplates('Coffee', limit)
    tmpl = call_and_ret(get_templates)
    return len(tmpl) == limit


@magnitude(norm=1, big=5, huge=600)
def test_query_pages(limit):
    qp_types = GetQueryPage.known_qps
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


@magnitude(norm=20, big=550, huge=2000)
def test_recent_changes(limit):
    get_recent_changes = GetRecentChanges(limit)
    recent_changes = call_and_ret(get_recent_changes)
    return len(recent_changes) == limit


def create_parser():
    parser = ArgumentParser(description='Test operations')
    parser.add_argument('functions', nargs='*')
    parser.add_argument('--pdb_all', '-a', action='store_true')
    parser.add_argument('--no_pdb_int', action='store_true')
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

    if not args.no_pdb_int:
        import signal
        def pdb_int_handler(signal, frame):
            import pdb;pdb.set_trace()
        signal.signal(signal.SIGINT, pdb_int_handler)

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
    pprint(results)
    print
    failures = [k for k, v in results.items() if not v and v is not None]
    if failures:
        print '-- the following tests failed: %r' % failures
    else:
        print '++ all tests passed'

    return results

if __name__ == '__main__':
    main()
