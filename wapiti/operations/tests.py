# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import base
from category import (GetCategory,
                      GetSubcategoryInfos,
                      GetFlattenedCategory,
                      GetCategoryRecursive,
                      GetCategoryPagesRecursive)
from rand import GetRandom
from protection import GetProtections
from links import (GetBacklinks,
                   GetLanguageLinks,
                   GetInterwikiLinks,
                   GetExternalLinks)
from feedback import GetFeedbackV4, GetFeedbackV5
from revisions import (GetRevisionInfos,
                       GetCurrentContent,
                       GetCurrentTalkContent)
from templates import GetTranscludes

PDB_ALL = False
PDB_ERROR = False
DO_PRINT = False


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
        print repr(disp)[:50] + '...'
    return ret


def test_category_basic():
    get_2k_featured = GetCategory('Featured_articles', 2000)
    pages = call_and_ret(get_2k_featured)
    return len(pages) == 2000


def test_nonexistent_cat_error():
    '''
    Should return invalidcategory error
    {"servedby":"mw1204","error":{"code":"gcminvalidcategory","info":"The category name you entered is not valid"}}
    ```
    nonexistent_cat = GetCategory('DoesNotExist', 100)
    pages = call_and_ret(nonexistent_cat)
    '''
    pass


def test_subcategory_infos():
    get_subcats = GetSubcategoryInfos('FA-Class_articles', 100)
    subcats = call_and_ret(get_subcats)
    return len(subcats) == 100


def test_category_recursive():
    get_2k_recursive = GetCategoryRecursive('Africa', 2000)
    pages = call_and_ret(get_2k_recursive)
    return len(pages) == 2000


def test_single_prot():
    get_coffee_prot = GetProtections('Coffee')
    prots = call_and_ret(get_coffee_prot)
    return len(prots) == 1


def test_multi_prots_list():
    get_prots = GetProtections(['Coffee', 'House'])
    prots = call_and_ret(get_prots)
    return len(prots) == 2


def test_multi_prots_str():
    get_prots = GetProtections('Coffee|House')
    prots = call_and_ret(get_prots)
    return len(prots) == 2


def test_nonexistent_prot():
    '''
    returns 'missing' and negative id
    get_nonexistent_prot = GetProtections('DoesNotExist')
    prots = call_and_ret(get_nonexistent_prot)
    '''
    pass


def test_backlinks():
    get_bls = GetBacklinks('Coffee', 10)
    bls = call_and_ret(get_bls)
    '''
    Nonexistent title returns []
    '''
    return len(bls) == 10


def test_random():
    get_fifty_random = GetRandom(50)
    pages = call_and_ret(get_fifty_random)
    return len(pages) == 50


def test_lang_links():
    get_coffee_langs = GetLanguageLinks('Coffee', 5)
    lang_list = call_and_ret(get_coffee_langs)
    return len(lang_list) == 5


def test_nonexistent_lang_links():
    '''
    returns 'missing' and negative id
    get_nonexistent_ll = GetLanguageLinks('DoesNotExist')
    lang_list = call_and_ret(get_nonexistent_ll)
    '''
    pass


def test_interwiki_links():
    get_coffee_iwlinks = GetInterwikiLinks('Coffee', 5)
    iw_list = call_and_ret(get_coffee_iwlinks)
    return len(iw_list) == 5


def test_nonexistent_iw_links():
    '''
    returns 'missing' and negative id
    get_nonexistent_iwl = GetInterwikiLinks('DoesNotExist')
    iw_list = call_and_ret(get_nonexistent_iwl)
    '''
    pass


def test_external_links():
    get_coffee_elinks = GetExternalLinks('Croatian War of Independence', 300)
    el_list = call_and_ret(get_coffee_elinks)
    assert len(set(el_list)) == len(el_list)
    return len(el_list) == 300


def test_feedback_v4():
    get_v4 = GetFeedbackV4(604727)
    v4_list = call_and_ret(get_v4)
    return len(v4_list) > 1


def test_feedback_v5():
    get_v5 = GetFeedbackV5(604727)
    v5_list = call_and_ret(get_v5)
    return isinstance(v5_list, list)


def test_revisions():
    get_revs = GetRevisionInfos('Coffee', 10)
    rev_list = call_and_ret(get_revs)
    return len(rev_list) == 10


def test_missing_revisions():
    get_revs = GetRevisionInfos('Coffee_lololololol')
    rev_list = call_and_ret(get_revs)
    '''
    Should return 'missing' and negative pageid
    '''
    return len(rev_list) == 0


def test_transclusions():
    get_transcludes = GetTranscludes('Template:ArticleHistory', 20)
    tr_list = call_and_ret(get_transcludes)
    '''
    Nonexistent title returns []
    '''
    return len(tr_list) == 20


def test_resolve_subjects():
    get_res_transcludes = GetTranscludes('Template:ArticleHistory',
                                         100,
                                         resolve_to_subject=True)
    tr_list = call_and_ret(get_res_transcludes)
    return len(tr_list) == 100 and all([t.is_subject_page for t in tr_list])


def test_current_content():
    get_page = GetCurrentContent('Coffee')
    page = call_and_ret(get_page)
    return page[0].title == 'Coffee'


def test_current_content_redirect():
    get_page = GetCurrentContent('Obama')
    page = call_and_ret(get_page)
    return page[0].title == 'Barack Obama'


def test_current_talk_content():
    get_talk_page = GetCurrentTalkContent('Obama')
    page = call_and_ret(get_talk_page)
    return page[0].title == 'Talk:Barack Obama'


def test_flatten_category():
    get_flat_cat = GetFlattenedCategory('Africa', 2000)
    cat_infos = call_and_ret(get_flat_cat)
    assert len(set([ci.title for ci in cat_infos])) == len(cat_infos)
    return len(cat_infos) == 2000


def test_cat_mem_namespace():
    get_star_portals = GetCategory('Astronomy_portals', 10, namespace=[100])
    portals = call_and_ret(get_star_portals)
    return len(portals) == 10


def test_cat_pages_recursive():
    get_cat_pages_rec = GetCategoryPagesRecursive('Africa',
                                                  600,
                                                  resolve_to_subject=True)
    pages = call_and_ret(get_cat_pages_rec)
    return len(pages) == 600


def main():
    tests = dict([(k, v) for k, v in globals().items()
                  if callable(v) and k.startswith('test_')])
    results = dict([(k, v()) for k, v in tests.items()])
    return results


def _main():
    call_and_ret(test_external_links)


if __name__ == '__main__':
    PDB_ALL = False
    PDB_ERROR = True
    DO_PRINT = True
    from pprint import pprint
    pprint(main())
