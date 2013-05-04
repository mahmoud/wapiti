"""\
A very simple Mediawiki template parser that turns template
references into nested key-value, partial()-like objects.

Thanks to Mark Williams for 95% of this.
"""

import re
import pprint
import itertools
import functools

from collections import namedtuple

Token = namedtuple('Token', 'name value')

Arg = namedtuple('Arg', 'value')
Kwarg = namedtuple('Kwarg', 'key value')


def atomize(token):
    token = token.strip()
    converters = [int, float, str]

    for convert in converters:
        try:
            return convert(token)
        except ValueError:
            pass
    else:
        raise RuntimeError('unknown token {0}'.format(token))


lex = re.Scanner([(r'\{\{', lambda s, t: Token('BEGIN', t)),
                  (r'\}\}', lambda s, t: Token('END', t)),
                  (r'[^|{}=]+', lambda s, t: Token('ATOM', atomize(t))),
                  (r'=', lambda s, t: Token('EQUAL', t)),
                  (r'\|', lambda s, t: Token('PARAMETER', t))])


class TokenStream(object):

    def __init__(self, tokens):
        self.iterator = iter(tokens)
        self.pushed = None

    def __iter__(self):
        return self

    def next(self):
        if self.pushed is not None:
            pushed, self.pushed = self.pushed, None
            return pushed
        return next(self.iterator)


def parse(s):
    tokens = TokenStream(lex.scan(s)[0])

    return match_template(tokens)


def advance(tokens):
    return next(tokens, Token(None, None))


def match_template(tokens):
    token = advance(tokens)
    template = {}

    if token.name != 'BEGIN':
        tokens.pushed = token
        return template

    name = match_atom(tokens)
    if name is None:
        name = match_template(tokens)

    template['name'] = name

    match_parameters(template, tokens)

    match_end(tokens)

    return template


def match_atom(tokens):
    token = advance(tokens)
    if token.name != 'ATOM':
        tokens.pushed = token
        return None

    return token.value


def match_parameters(template, tokens):
    pairs = []

    def manage_pairs():
        while True:
            idx, value = yield
            if value is None:
                continue
            if not idx:
                pair = [None, None]
                pairs.append(pair)
            pair[idx] = value

    pair_manager = manage_pairs()
    next(pair_manager)

    cycler = functools.partial(itertools.cycle, [0, 1])

    while True:
        token = advance(tokens)
        if token.name == 'PARAMETER':
            idx_cycle = cycler()
            pair_manager.send((0, None))
        elif token.name == 'ATOM':
            pair_manager.send((next(idx_cycle), token.value))
        elif token.name == 'BEGIN':
            tokens.pushed = token
            pair_manager.send((next(idx_cycle), match_template(tokens)))
        elif token.name == 'EQUAL':
            continue
        else:
            break
    tokens.pushed = token

    template['parameters'] = [Arg(pair[0]) if pair[1] is None else Kwarg(*pair)
                              for pair in pairs]


def match_end(tokens):
    token = advance(tokens)
    assert token.name == 'END', 'expected end but got {0}'.format(token.name)


test = '''{{cite web
| url = [http://www.census.gov/geo/www/gazetteer/files/Gaz_places_national.txt U.S. Census]
| publisher=US Census Bureau
| accessdate =2011
| title = U.S. Census
}}'''

test = '''{{citation
| last = Terplan
| first = Egon
| title = Organizing for Economic Growth
| subtitle = A new approach to business attraction and retention in San Francisco
| work=SPUR Report
| publisher=San Francisco Planning and Urban Research Association
| date = June 7, 2010
| url = http://www.spur.org/publications/library/report/organizing-economic-growth
| quote = During the 1960s and 1970s San Francisco's historic maritime industry relocated to Oakland. ... San Francisco remained a center for business and professional services (such as consulting, law, accounting and finance) and also successfully developed its tourism sector, which became the leading local industry.
| accessdate = January 5, 2013
}}'''


test = '''{{climate chart
| San Francisco
|46.2|56.9|4.5
|48.1|60.2|4.61
|49.1|62.9|3.26
|49.9|64.3|1.46
|51.6|65.6|0.7
|53.3|67.9|0.16
|54.6|68.2|0
|55.6|69.4|0.06
|55.7|71.3|0.21
|54.3|70.4|1.13
|50.7|63.2|3.16
|46.7|57.3|4.56
|float=right
|clear=none
|units=imperial}}'''
pprint.pprint(parse(test))


# >>> {'name': 'climate chart',
#  'parameters': [Arg(value='San Francisco'),
#                 Arg(value=46.2),
#                 Arg(value=56.9),
#                 Arg(value=4.5),
#                 Arg(value=48.1),
#                 Arg(value=60.2),
#                 Arg(value=4.61),
#                 Arg(value=49.1),
#                 Arg(value=62.9),
#                 Arg(value=3.26),
#                 Arg(value=49.9),
#                 Arg(value=64.3),
#                 Arg(value=1.46),
#                 Arg(value=51.6),
#                 Arg(value=65.6),
#                 Arg(value=0.7),
#                 Arg(value=53.3),
#                 Arg(value=67.9),
#                 Arg(value=0.16),
#                 Arg(value=54.6),
#                 Arg(value=68.2),
#                 Arg(value=0),
#                 Arg(value=55.6),
#                 Arg(value=69.4),
#                 Arg(value=0.06),
#                 Arg(value=55.7),
#                 Arg(value=71.3),
#                 Arg(value=0.21),
#                 Arg(value=54.3),
#                 Arg(value=70.4),
#                 Arg(value=1.13),
#                 Arg(value=50.7),
#                 Arg(value=63.2),
#                 Arg(value=3.16),
#                 Arg(value=46.7),
#                 Arg(value=57.3),
#                 Arg(value=4.56),
#                 Kwarg(key='float', value='right'),
#                 Kwarg(key='clear', value='none'),
#                 Kwarg(key='units', value='imperial')]}
