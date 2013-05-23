# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base

from models import PageIdentifier
from category import GetSubcategoryInfos

from revisions import GetCurrentContent, GetPageRevisionInfos
from meta import GetSourceInfo


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


def test_get_meta():
    get_source_info = GetSourceInfo()
    meta = get_source_info()
    assert meta
