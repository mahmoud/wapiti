# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wapiti import WapitiClient
from operations.tests import call_and_ret


def test_client_basic():
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    cat_pages = client.get_category_recursive('Africa', 1000)
    return len(cat_pages) == 1000


def main():
    return call_and_ret(test_client_basic)


if __name__ == '__main__':
    print main()
