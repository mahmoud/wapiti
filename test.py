from wapiti import GetCategory


def test_category_basic():
    get_2k_featured = GetCategory('Featured_articles', 2000)
    try:
        pages = get_2k_physics()
    except Exception as e:
        if DO_PDB:
            import pdb;pdb.post_portem()
        raise
    if DO_PDB:
        import pdb;pdb.set_trace()
    return len(pages) == 2000


def main():
    test_category_basic()

if __name__ == '__main__':
    DO_PDB = True
    main()
