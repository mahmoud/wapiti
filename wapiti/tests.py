# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from argparse import ArgumentParser
from functools import wraps

from wapiti import WapitiClient
from operations import tests

from functools import partial

DEFAULT_MAGNITUDE = 'norm'


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


def test_client_basic(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    return len(client.source_info.namespace_map) > 10


@magnitude(norm=20, big=550, huge=2000)
def test_cat(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_africa = partial(client.get_category_recursive, 'Africa', limit)
    cat_pages = call_and_ret(get_africa)
    return len(cat_pages) == limit


def test_unicode_title(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_beyonce = partial(client.get_current_content, "Beyoncé Knowles")
    beyonce = call_and_ret(get_beyonce)
    return bool(beyonce)


@magnitude(norm=20, big=550, huge=2000)
def test_category_basic(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_2k_featured = partial(client.get_category, 'Featured_articles', limit)
    pages = call_and_ret(get_2k_featured)
    return len(pages) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_subcategory_infos(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_subcats = partial(client.get_subcategory_infos, 'FA-Class_articles', limit)
    subcats = call_and_ret(get_subcats)
    return len(subcats) == limit


def test_all_category_infos(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_all_cats = partial(client.get_all_category_infos, 501)
    all_cats = call_and_ret(get_all_cats)
    return len(all_cats) == 501


@magnitude(norm=10, big=1000, huge=10000)
def test_category_recursive(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_limit_recursive = partial(client.get_category_recursive, 'Africa', limit)
    pages = call_and_ret(get_limit_recursive)
    return len(pages) == limit


def test_single_prot(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_coffee_prot = partial(client.get_protections, 'Coffee')
    prots = call_and_ret(get_coffee_prot)
    return len(prots) == 1


def test_multi_prots_list(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_prots = partial(client.get_protections, ['Coffee', 'House'])
    prots = call_and_ret(get_prots)
    return len(prots) == 2


def test_multi_prots_str(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_prots = partial(client.get_protections, 'Coffee|House')
    prots = call_and_ret(get_prots)
    return len(prots) == 2


@magnitude(norm=20, big=550, huge=2000)
def test_backlinks(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_bls = partial(client.get_backlinks, 'Coffee', limit)
    bls = call_and_ret(get_bls)
    '''
    Nonexistent title returns []
    '''
    return len(bls) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_random(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_fifty_random = partial(client.get_random, limit)
    pages = call_and_ret(get_fifty_random)
    return len(pages) == limit


@magnitude(norm=5, big=550, huge=2000)
def test_lang_links(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_coffee_langs = partial(client.get_language_links, 'Coffee', limit)
    lang_list = call_and_ret(get_coffee_langs)
    return len(lang_list) == limit


@magnitude(norm=5, big=550, huge=2000)
def test_interwiki_links(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_coffee_iwlinks = partial(client.get_interwiki_links, 'Coffee', limit)
    iw_list = call_and_ret(get_coffee_iwlinks)
    return len(iw_list) == limit

@magnitude(norm=20, big=550, huge=2000)
def test_external_links(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_coffee_elinks = partial(client.get_external_links, 'Croatian War of Independence', limit)
    el_list = call_and_ret(get_coffee_elinks)
    assert len(set(el_list)) == len(el_list)
    return len(el_list) == limit


#def test_feedback_v4(limit):  # no longer available, see feedback.py for info
#    get_v4 = GetFeedbackV4('604727')
#    v4_list = call_and_ret(get_v4)
#    return len(v4_list) > 1


def test_feedback_v5(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_v5 = partial(client.get_feedback_v5, '604727')  # TODO: support ints
    v5_list = call_and_ret(get_v5)
    return isinstance(v5_list, list)


@magnitude(norm=10, big=550, huge=2000)
def test_revisions(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_revs = partial(client.get_page_revision_infos, 'Coffee', 10)
    rev_list = call_and_ret(get_revs)
    return len(rev_list) == 10


def test_missing_revisions(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_revs = partial(client.get_page_revision_infos, 'Coffee_lololololol')
    rev_list = call_and_ret(get_revs)
    '''
    Should return 'missing' and negative pageid
    '''
    return len(rev_list) == 0


@magnitude(norm=20, big=550, huge=2000)
def test_transclusions(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_transcludes = partial(client.get_transcludes, 'Template:ArticleHistory', limit)
    tr_list = call_and_ret(get_transcludes)
    '''
    Nonexistent title returns []
    '''
    return len(tr_list) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_all_transcludes(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_all_transcludes = partial(client.get_all_transcludes, limit)
    tr_list = call_and_ret(get_all_transcludes)
    return len(tr_list) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_resolve_subjects(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_res_transcludes = partial(client.get_transcludes, 'Template:ArticleHistory',
                                         limit,
                                         resolve_to_subject=True)
    tr_list = call_and_ret(get_res_transcludes)
    tr_list = [t.get_subject_info() for t in tr_list]
    return len(tr_list) == limit and all([t.is_subject_page for t in tr_list])


def test_current_content(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_page = partial(client.get_current_content, 'Coffee')
    page = call_and_ret(get_page)
    return page[0].title == 'Coffee'


def test_current_content_redirect(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_page = partial(client.get_current_content, 'Obama')
    page = call_and_ret(get_page)
    return page[0].title == 'Barack Obama'


def test_current_talk_content(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_talk_page = partial(client.get_current_talk_content, 'Obama')
    page = call_and_ret(get_talk_page)
    return page[0].title == 'Talk:Barack Obama'


@magnitude(norm=20, big=550, huge=2000)
def test_flatten_category(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_flat_cat = partial(client.get_flattened_category, 'History', limit)
    cat_infos = call_and_ret(get_flat_cat)
    assert len(set([ci.title for ci in cat_infos])) == len(cat_infos)
    return len(cat_infos) == limit


@magnitude(norm=10, big=550, huge=2000)
def test_cat_mem_namespace(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_star_portals = partial(client.get_category, 'Astronomy_portals', limit, namespace=['100'])
    portals = call_and_ret(get_star_portals)
    return len(portals) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_cat_pages_recursive(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_cat_pages_rec = partial(client.get_category_pages_recursive, 'Africa',
                                                  limit,
                                                  resolve_to_subject=True)
    pages = call_and_ret(get_cat_pages_rec)
    return len(pages) == limit


@magnitude(norm=11, big=550, huge=2000)
def test_cat_list(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_cat_list = partial(client.get_category_list, 'Physics', limit)
    pages = call_and_ret(get_cat_list)
    return len(pages) == limit


@magnitude(norm=4, big=550, huge=2000)
def test_get_images(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_imgs = partial(client.get_images, 'Coffee', limit)
    imgs = call_and_ret(get_imgs)
    return len(imgs) == limit


@magnitude(norm=5, big=550, huge=2000)
def test_get_links(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_links = partial(client.get_links, 'Coffee', limit)
    links = call_and_ret(get_links)
    return len(links) == limit


def test_coordinates(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_coordinates = partial(client.get_coordinates, ['White House', 'Golden Gate Bridge', 'Mount Everest'])
    coords = call_and_ret(get_coordinates)
    return len(coords) == 3


def test_geosearch(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    geosearch = partial(client.geo_search, ('37.8197', '-122.479'))
    geo = call_and_ret(geosearch)
    return len(geo) > 1


@magnitude(norm=20, big=550, huge=2000)
def test_get_user_contribs(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_contribs = partial(client.get_user_contribs, 'Jimbo Wales', limit)
    contribs = call_and_ret(get_contribs)
    return len(contribs) == limit


def test_get_meta(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_source_info = client.get_source_info
    meta = call_and_ret(get_source_info)
    return len(meta[0].interwiki_map) > 1


def test_get_revision_infos(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_revisions = partial(client.get_revision_infos, ['538903663', '539916351', '531458383'])
    rev_infos = call_and_ret(get_revisions)
    return len(rev_infos) == 3


@magnitude(norm=20, big=550, huge=2000)
def test_get_contrib_rev_infos(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_contrib_rev_infos = partial(client.get_user_contrib_revisions, 'Jimbo Wales', limit)
    contrib_rev_infos = call_and_ret(get_contrib_rev_infos)
    return len(contrib_rev_infos) == limit


def test_get_image_info(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_image_info = partial(client.get_image_infos, 'File:Logo.gif')
    image_info = call_and_ret(get_image_info)
    return image_info[0].url == 'http://upload.wikimedia.org/wikipedia/en/e/ea/Logo.gif'


@magnitude(norm=20, big=550, huge=2000)
def test_get_all_image_infos(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_all_img = partial(client.get_all_image_infos, limit)
    all_imgs = call_and_ret(get_all_img)
    return len(all_imgs) == limit


@magnitude(norm=20, big=550, huge=2000)
def test_get_templates(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_templates = partial(client.get_templates, 'Coffee', limit)
    tmpl = call_and_ret(get_templates)
    return len(tmpl) == limit


@magnitude(norm=1, big=5, huge=600)
def test_query_pages(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    from operations.misc import GetQueryPage as gqp
    qp_types = gqp.known_qps
    ret = []
    for qpt in qp_types:
        get_pages = partial(client.get_query_page, qpt, limit)
        ret.extend(call_and_ret(get_pages))
    return len(ret) == limit * len(qp_types)


def test_nonexistent_query_page(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    try:
        non_existent_qp = partial(client.get_query_page, 'FakeQueryPage')
        call_and_ret(non_existent_qp)
    except ValueError:
        return True


@magnitude(norm=20, big=550, huge=2000)
def test_recent_changes(limit):
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    get_recent_changes = partial(client.get_recent_changes, limit)
    recent_changes = call_and_ret(get_recent_changes)
    return len(recent_changes) == limit


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
    from pprint import pprint
    pprint(main())
