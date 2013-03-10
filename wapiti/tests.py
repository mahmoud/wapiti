# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wapiti import WapitiClient
from operations import tests
from operations.tests import call_and_ret

from functools import partial


def test_client_basic():
    client = WapitiClient('mahmoudrhashemi@gmail.com')
    return len(client.source_info.namespace_map) > 10

#     get_africa = partial(client.get_category_recursive, 'Africa', 100)
#    cat_pages = call_and_ret(get_africa)


def main():
    return test_client_basic()


if __name__ == '__main__':
    tests.PDB_ALL = True
    tests.PDB_ERROR = True
    print main()
