# -*- coding: utf-8 -*-
"""\
A very simple Mediawiki template parser that turns template
references into nested key-value objects.

From a Python perspective, one can think of TemplateReferences as the
``partial()``s to MediaWiki templates.

Thanks to Mark Williams for drafting this.

TODO
----

* Save original TemplateReference source
* Nesting robustness
  * Autoclose template?
* Merge TemplateReference and ProtoTemplateRef
* .add_item() for order preservation
* items(), keys(), etc.
* parse out limited html for attempted int/float extraction
* traverse() helper
* strip wiki syntax
* .links, .tables, .subtemplates
"""
from __future__ import unicode_literals

import re
import itertools
"""
Notes
-----

- everything inside html comments is ignored
- no html in keys
- html in values
- '=' only allowed after key if no '=' encountered yet

_transitiony_things = \
         {'template': {'key': ['=', '|', '}}'], 'value': ['|', '}}']},
          'html_comment': ['-->'],
          'link': [']]'],
          'table': ['|}']}
"""


def is_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    return True


def is_scalar(obj):
    return not is_iterable(obj) or isinstance(obj, basestring)


class TemplateReference(object):
    def __init__(self, name, args, kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def from_string(cls, text):
        tokens = tokenize(text)
        return [t for t in parse(tokens) if isinstance(t, cls)][0]  # blargh

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.name, self.args, self.kwargs)

    def __getitem__(self, key):
        try:
            return self.kwargs[key]
        except KeyError:
            raise KeyError('%r template has no key %r' % (self.name, key))
        """
        if is_scalar(val) or isinstance(val, TemplateReference):
            return val
        for subval in val:
            if subval
            try:
                return val[key]
            except KeyError:
                pass
        else:
            raise KeyError('%r template has no key %r' % (self.name, key))
        """

    def __iter__(self):
        return itertools.chain(iter(self.args), self.kwargs.iteritems())


def get_page_templates(source):
    tokens = tokenize(source)
    parsed = parse(tokens)
    return [t for t in parsed if isinstance(t, TemplateReference)]


class Token(object):
    def __init__(self, start_index, text):
        self.start_index = start_index
        self.text = text

    @classmethod
    def from_match(cls, match):
        return cls(start_index=match.start(), text=match.group())

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r)' % (cn, self.text)


class BufferToken(Token):
    pass


class CommentToken(BufferToken):
    pass


class LinkToken(BufferToken):
    pass


class TableToken(BufferToken):
    pass


class SepToken(Token):
    pass


class StartTemplateToken(Token):
    pass


class EndTemplateToken(SepToken):
    pass


LEXICON = \
    [(r'(\[\[.+?\]\])', lambda m, t: LinkToken.from_match(m)),
     (r'(\{\|.+?\|\})', lambda m, t: TableToken.from_match(m)),
     (r'(<!--.+?-->)', lambda m, t: CommentToken.from_match(m)),
     (r'\{\{', lambda m, t: StartTemplateToken.from_match(m)),
     (r'\}\}', lambda m, t: EndTemplateToken.from_match(m)),
     (r'=', lambda m, t: SepToken.from_match(m)),
     (r'\|', lambda m, t: SepToken.from_match(m))]


def build_scanner(lexicon, flags=0):
    import sre_parse
    import sre_compile
    from sre_constants import BRANCH, SUBPATTERN
    # combine phrases into a compound pattern
    p = []
    s = sre_parse.Pattern()
    s.flags = flags
    for phrase, action in lexicon:
        p.append(sre_parse.SubPattern(s, [
            (SUBPATTERN, (len(p) + 1, sre_parse.parse(phrase, flags))),
        ]))
    s.groups = len(p) + 1
    p = sre_parse.SubPattern(s, [(BRANCH, (None, p))])
    scanner = sre_compile.compile(p)
    return scanner


def tokenize(source, lexicon=None):
    lexicon = lexicon or LEXICON
    lex = build_scanner(lexicon, re.DOTALL)
    all_tokens = []
    start, end, prev_end = 0, 0, 0
    for match in lex.finditer(source):
        start, end = match.start(), match.end()
        if prev_end < start:
            all_tokens.append(BufferToken(start, source[prev_end:start]))
        action = lexicon[match.lastindex - 1][1]
        if callable(action):
            # TODO: what should the callbacks want?
            cur_token = action(match, match.group())
            all_tokens.append(cur_token)
        else:
            raise TypeError('expected callable callback, not %r' % (action,))
        prev_end = end
    if prev_end < len(source):
        all_tokens.append(BufferToken(prev_end, source[prev_end:]))
    return all_tokens


def cond_join(items, sep='', cond=None):
    # TODO: messsss
    if cond is None:
        cond = lambda s: isinstance(s, basestring)
    ret, tmp_buffer = [], []
    for item in items:
        if cond(item):
            tmp_buffer.append(item.strip())  # TODO: remove strip()
        else:
            if tmp_buffer:
                ret.append(sep.join(tmp_buffer))
                tmp_buffer = []
            ret.append(item)
    if tmp_buffer:
        ret.append(sep.join(tmp_buffer))
    return ret


def process_korv(korv):
    if not korv:
        return ''
    # TODO: need fancy split() (for <str> <tmpl> <str> <tmpl>)
    korv = [_kv for _kv in cond_join(korv) if _kv]
    if not korv:
        return ''
    elif len(korv) == 1:
        korv = korv[0]
    if isinstance(korv, basestring):
        korv = korv.strip()
        converters = [int, float, unicode]
        for convert in converters:
            try:
                return convert(korv)
            except ValueError:
                pass
            else:
                raise ValueError('unknown key or value {0}'.format(korv))
    return korv


class ProtoTemplateRef(object):
    def __init__(self, start_token):
        self.start_token = start_token
        self.args = []
        self.kwargs = []
        self.cur_val = []
        self.tmp_key = None
        self.end_token = None

    def to_template_ref(self):
        args = [process_korv(a) for a in self.args]
        name, args = args[0], args[1:]
        kwargs = [(process_korv(k), process_korv(v)) for (k, v) in self.kwargs]
        kwargs = dict(kwargs)
        return TemplateReference(name, args, kwargs)

    def __repr__(self):
        cn = self.__class__.__name__
        if not self.args:
            return '%s(%r)' % (cn, self.start_token,)
        return ('%s(%r, %r, %r)' %
                (cn, self.args[0], self.args[1:], self.kwargs))


def parse(tokens):
    ret = []
    pts = []  # ProtoTemplate stack
    interstish = []
    for token in tokens:
        if isinstance(token, CommentToken):
            continue  # TODO: save comments?
        if isinstance(token, StartTemplateToken):
            if interstish:
                ret.append(''.join(interstish))
                interstish = []
            pts.append(ProtoTemplateRef(token))
            continue
        elif not pts:
            interstish.append(token.text)
            continue
        else:
            cpt = pts[-1]

        if isinstance(token, SepToken):
            tmp_key, cur_val = cpt.tmp_key, cpt.cur_val
            #''.join(cpt.cur_buff).strip()
            if token.text == '|' or token.text == '}}':
                if tmp_key is None:
                    # cur_val is a value for a positional arg
                    cpt.args.append(cur_val)
                else:
                    # cur_val is a value for a keyword arg
                    cpt.kwargs.append((tmp_key, cur_val))
                    cpt.tmp_key = None
                cpt.cur_val = []
            elif token.text == '=' and tmp_key is None:
                # cur_val is a key
                cpt.tmp_key = ''.join(cur_val).strip()  # TODO: int()s?
                cpt.cur_val = []
            else:
                cpt.cur_val.append(token.text)
        else:
            # links and tables
            cpt.cur_val.append(token.text)

        if isinstance(token, EndTemplateToken):
            # create real Template
            pts.pop()
            cpt.end_token = token
            comp_tmpl = cpt.to_template_ref()
            if pts:
                pts[-1].cur_val.append(comp_tmpl)
            else:
                ret.append(comp_tmpl)
        # end loop

    return ret


_BASIC_CITE_TEST = '''{{cite web
| url = [http://www.census.gov/geo/www/gazetteer/files/Gaz_places_national.txt U.S. Census]
| publisher=US Census Bureau
| accessdate =2011
| title = U.S. Census
}}'''

_BIGGER_CITE_TEST = '''{{citation
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

_SF_CLIMATE_TEST = '''{{climate chart
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

_SF_INFOBOX = '''{{Infobox settlement
|name = San Francisco
|official_name = City and County of San Francisco
|nickname = ''The City by the Bay''; ''Fog City''; ''S.F.''; ''Frisco'';<ref name="Frisco okay" /><ref name="Don't Call It Frisco" /><ref name="Frisco" /><ref name="Friscophobia" /> ''The City that Knows How'' (''antiquated'');<ref name="The City that Knows How" /> ''Baghdad by the Bay'' (''antiquated'');<ref name="Baghdad by the Bay" /> ''The Paris of the West''<ref name="The Paris of the West" />
| settlement_type = [[Consolidated city-county|City and county]]
| motto = ''Oro en Paz, Fierro en Guerra''<br />(English: "Gold in Peace, Iron in War")
| image_skyline = SF From Marin Highlands3.jpg
| imagesize = 280px
| image_caption = San Francisco from the Marin Headlands, with the Golden Gate Bridge in the foreground
| image_flag = Flag of San Francisco.svg
| flag_size = 100px
| image_seal = Sfseal.png
| seal_size = 100px
| image_map = California county map (San Francisco County enlarged).svg
| mapsize = 200px
| map_caption = Location of San Francisco in California
| pushpin_map = USA2
| pushpin_map_caption = Location in the United States
<!-- Location ------------------>
| coordinates_region = US-CA
| subdivision_type = [[List of countries|Country]]
| subdivision_name = {{USA}}
| subdivision_type1 = [[Political divisions of the United States|State]]
| subdivision_name1 = {{flag|California}}

<!-- Politics ----------------->
| government_type = [[Mayor-council government|Mayor-council]]
| governing_body = [[San Francisco Board of Supervisors|Board of Supervisors]]
| leader_title = [[Mayor of San Francisco]]
| leader_name = [[Ed Lee (politician)|Ed Lee]]
| leader_title1 = [[San Francisco Board of Supervisors|Board of Supervisors]]
| leader_name1 = {{Collapsible list
| title = Supervisors
| frame_style = border:none; padding: 0;
| list_style = text-align:left;
| 1 = [[Eric Mar]]
| 2 = [[Mark Farrell (politician)|Mark Farrell]]
| 3 = [[David Chiu (politician)|David Chiu]]
| 4 = [[Katy Tang]]
| 5 = [[London Breed]]
| 6 = [[Jane Kim]]
| 7 = [[Norman Yee]]
| 8 = [[Scott Wiener]]
| 9 = [[David Campos]]
| 10 = [[Malia Cohen]]
| 11 = [[John Avalos]]}}
| leader_title2 = [[California State Assembly]]
| leader_name2 = [[Tom Ammiano]] ([[California Democratic Party|D]])<br />[[Phil Ting]] ([[California Democratic Party|D]])
| leader_title3 = [[California State Senate]]
| leader_name3 = [[Leland Yee]] ([[California Democratic Party|D]])<br />[[Mark Leno]] ([[California Democratic Party|D]])
| leader_title4 = [[United States House of Representatives]]
| leader_name4 = [[Nancy Pelosi]] ([[Democratic Party (United States)|D]])<br />[[Jackie Speier]] ([[Democratic Party (United States)|D]])
| established_title = Founded
| established_date = June 29, 1776
| established_title1 = [[Municipal incorporation|Incorporated]]
| established_date1 = April 15, 1850<ref>{{cite web
| url = http://www6.sfgov.org/index.aspx?page=4
| title = San Francisco: Government
| publisher = SFGov.org
| accessdate =March 8, 2012
| quote = San Francisco was incorporated as a City on April 15th, 1850 by act of the Legislature.}}</ref>
| founder = Lieutenant [[José Joaquin Moraga]] and [[Francisco Palóu]]
| named_for = [[St. Francis of Assisi]]

<!-- Area------------------>
|area_magnitude =
| unit_pref = US
| area_footnotes = <ref name="Census 2010-GCT-PH1" />
| area_total_sq_mi = 231.89
| area_land_sq_mi = 46.87
| area_water_sq_mi = 185.02
| area_water_percent = 79.79
| area_note =
| area_metro_sq_mi = 3524.4

<!-- Elevation ------------------------->
| elevation_ft = 52
| elevation_max_ft = 925
| elevation_min_ft = 0

<!-- Population ----------------------->
| population_as_of = 2012
| population_footnotes =
| population_total = 815358 <ref>http://voices.yahoo.com/largest-us-cities-population-size-2012-6453656.html?cat=16</ref>
| population_density_sq_mi = 17179.2
| population = [[Combined statistical area|CSA]]: 8371000
| population_metro = 4335391
| population_urban = 3273190
| population_demonym = San Franciscan

<!-- General information --------------->
| timezone = [[Pacific Time Zone|Pacific Standard Time]]
| utc_offset = -8
| timezone_DST = [[Pacific Time Zone|Pacific Daylight Time]]
| utc_offset_DST = -7
| latd = 37
| latm = 47
| latNS = N
| longd = 122
| longm = 25
| longEW = W
| coordinates_display = 8

<!-- Area/postal codes & others -------->
| postal_code_type = [[ZIP Code]]
| postal_code = 94101–94112, 94114–94147, 94150–94170, 94172, 94175, 94177
| area_code = [[Area code 415|415]]
| blank_name = [[Federal Information Processing Standard|FIPS code]]
| blank_info = 06-67000
| blank1_name = [[Federal Information Processing Standard|FIPS code]]
| blank1_info = 06-075
| blank2_name = [[Geographic Names Information System|GNIS]] feature ID
| blank2_info = 277593
| website = {{URL|http://www.sfgov.org/}}
| footnotes =
}}
'''


_ALL_TEST_STRS = [_BASIC_CITE_TEST,
                  _BIGGER_CITE_TEST,
                  _SF_CLIMATE_TEST,
                  _SF_INFOBOX]


def _main():
    import pprint
    ret = []
    try:
        for test in _ALL_TEST_STRS:
            ret.append(TemplateReference.from_string(test))
            pprint.pprint(ret[-1])
        sf_infobox_tmpl = TemplateReference.from_string(_SF_INFOBOX)
        print 'Testing accessor:', sf_infobox_tmpl['leader_name1']['title']
    except Exception as e:
        print e
        import pdb
        pdb.post_mortem()
        raise

    return ret


if __name__ == '__main__':
    _main()
