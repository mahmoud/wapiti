from wapiti import GetCategory, GetRandom

PDB_ALL = False
PDB_ERROR = False

def call_and_ret(func):
    try:
        ret = func()
    except Exception as e:
        if PDB_ERROR:
            import pdb;pdb.post_mortem()
        raise
    if PDB_ALL:
        import pdb;pdb.set_trace()
    return ret


def test_category_basic():
    get_2k_featured = GetCategory('Featured_articles', 2000)
    pages = call_and_ret(get_2k_featured)
    return len(pages) == 2000


def test_random():
    get_fifty_random = GetRandom(50)
    pages = call_and_ret(get_fifty_random)
    return len(pages) == 50


def main():
    tests = dict([(k, v) for k, v in globals().items()
                  if callable(v) and k.startswith('test_')])
    results = dict([(k, v()) for k, v in tests.items()])
    return results


if __name__ == '__main__':
    PDB_ALL = False
    PDB_ERROR = True
    print main()
