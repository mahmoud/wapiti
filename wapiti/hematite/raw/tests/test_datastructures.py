from hematite.compat.dictutils import OMD
from hematite.raw import datastructures as D


def test_Headers():
    """Headers should be case insensitive to queries but also preserve
    their content's original case"""

    upper_a = [('A', 1), ('b', 2), ('a', 3)]
    lower_a = [('a', 1), ('b', 2), ('A', 3)]

    def _test_assertions(upper_a_headers, lower_a_headers):
        assert upper_a_headers.items(multi=True, preserve_case=True) == upper_a
        assert lower_a_headers.items(multi=True, preserve_case=True) == lower_a

        lower1 = [(k.lower(), v) for k, v in upper_a]
        assert upper_a_headers.items(multi=True, preserve_case=False) == lower1
        lower2 = [(k.lower(), v) for k, v in lower_a]
        assert lower_a_headers.items(multi=True, preserve_case=False) == lower2
        # sanity check
        assert lower1 == lower2

        items = upper_a_headers.items(multi=False, preserve_case=False)
        assert items == [('a', 3), ('b', 2)]
        items = lower_a_headers.items(multi=False, preserve_case=False)
        assert items == [('a', 3), ('b', 2)]

        assert upper_a_headers['a'] == 3
        assert lower_a_headers['a'] == 3

        assert upper_a_headers.get('a') == 3
        assert lower_a_headers.get('a') == 3

        assert upper_a_headers.getlist('a') == [1, 3]
        assert lower_a_headers.getlist('a') == [1, 3]

        assert upper_a_headers.get_cased_items('a') == [('A', 1), ('a', 3)]
        assert lower_a_headers.get_cased_items('a') == [('a', 1), ('A', 3)]

        dup_upper_a_headers = upper_a_headers.copy()
        dup_lower_a_headers = lower_a_headers.copy()

        assert dup_upper_a_headers.popall('a') == [1, 3]
        assert dup_lower_a_headers.popall('a') == [1, 3]

        dup_upper_a_headers = upper_a_headers.copy()
        dup_lower_a_headers = lower_a_headers.copy()

        assert dup_upper_a_headers.poplast() == 3
        assert dup_lower_a_headers.poplast() == 3

        dup_upper_a_headers.add('a', [4, 5], multi=True)
        dup_lower_a_headers.add('a', [4, 5], multi=True)

        expected = [('A', 1), ('b', 2), ('a', 4), ('a', 5)]
        assert dup_upper_a_headers.items(multi=True) == expected
        expected = [('a', 1), ('b', 2), ('a', 4), ('a', 5)]
        assert dup_lower_a_headers.items(multi=True) == expected

        assert upper_a_headers.setdefault('a', 6) == 3
        assert lower_a_headers.setdefault('a', 6) == 3

        assert dup_upper_a_headers.setdefault('c', 6) == 6
        assert 'c' in dup_upper_a_headers

        assert dup_lower_a_headers.setdefault('c', 6) == 6
        assert 'c' in dup_lower_a_headers

        dup_upper_a_headers['C'] = 7
        dup_lower_a_headers['C'] = 7

        assert dup_upper_a_headers['c'] == 7
        assert dup_lower_a_headers['c'] == 7

        dup_upper_a_headers = upper_a_headers.copy()
        dup_lower_a_headers = lower_a_headers.copy()

        dup_upper_a_headers.update(dup_upper_a_headers)
        dup_lower_a_headers.update(dup_lower_a_headers)

        dup_upper_a_headers.update(D.Headers([('c', 4)]))
        expected = upper_a + [('c', 4)]
        assert dup_upper_a_headers.items(multi=True) == expected

        dup_lower_a_headers.update(D.Headers([('C', 4)]))
        expected = lower_a + [('C', 4)]
        assert dup_lower_a_headers.items(multi=True) == expected

        dup_lower_a_headers.clear()
        dup_upper_a_headers.clear()

        assert not dup_upper_a_headers
        assert not dup_lower_a_headers

        assert dup_upper_a_headers.items() == []
        assert dup_lower_a_headers.items() == []

    upper_a_headers = D.Headers()
    for k, v in upper_a:
        upper_a_headers.add(k, v)

    lower_a_headers = D.Headers()
    for k, v in lower_a:
        lower_a_headers.add(k, v)

    _test_assertions(upper_a_headers, lower_a_headers)

    _test_assertions(D.Headers(upper_a), D.Headers(lower_a))


def test_Headers_extend_setdefault():
    def H():
        return D.Headers([('a', 1)])

    headers = H()
    headers.update(D.Headers([('A', 2)]))
    assert headers.items() == [('A', 2)]

    headers = H()
    headers.update(OMD([('b', 2), ('B', 3)]))
    assert headers.items(multi=True,
                         preserve_case=True) == [('a', 1),
                                                 ('b', 2),
                                                 ('B', 3)]

    headers = H()
    headers.update({'b': 2})
    assert headers.items() == [('a', 1), ('b', 2)]

    headers = H()
    headers.update([('a', 2), ('b', 3)])
    assert headers.items() == [('a', 2), ('b', 3)]

    headers = H()
    headers.update(b=2)
    assert headers.items() == [('a', 1), ('b', 2)]
