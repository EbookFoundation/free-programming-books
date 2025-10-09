"""
    pygments.filters
    ~~~~~~~~~~~~~~~~

    Module containing filter lookup functions and default
    filters.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from pip._vendor.pygments.token import String, Comment, Keyword, Name, Error, Whitespace, \
    string_to_tokentype
from pip._vendor.pygments.filter import Filter
from pip._vendor.pygments.util import get_list_opt, get_int_opt, get_bool_opt, \
    get_choice_opt, ClassNotFound, OptionError
from pip._vendor.pygments.plugin import find_plugin_filters


def find_filter_class(filtername):
    """Lookup a filter by name. Return None if not found."""
    if filtername in FILTERS:
        return FILTERS[filtername]
    for name, cls in find_plugin_filters():
        if name == filtername:
            return cls
    return None


def get_filter_by_name(filtername, **options):
    """Return an instantiated filter.

    Options are passed to the filter initializer if wanted.
    Raise a ClassNotFound if not found.
    """
    cls = find_filter_class(filtername)
    if cls:
        return cls(**options)
    else:
        raise ClassNotFound(f'filter {filtername!r} not found')


def get_all_filters():
    """Return a generator of all filter names."""
    yield from FILTERS
    for name, _ in find_plugin_filters():
        yield name


def _replace_special(ttype, value, regex, specialttype,
                     replacefunc=lambda x: x):
    last = 0
    for match in regex.finditer(value):
        start, end = match.start(), match.end()
        if start != last:
            yield ttype, value[last:start]
        yield specialttype, replacefunc(value[start:end])
        last = end
    if last != len(value):
        yield ttype, value[last:]


class CodeTagFilter(Filter):
    """Highlight special code tags in comments and docstrings.

    Options accepted:

    `codetags` : list of strings
       A list of strings that are flagged as code tags.  The default is to
       highlight ``XXX``, ``TODO``, ``FIXME``, ``BUG`` and ``NOTE``.

    .. versionchanged:: 2.13
       Now recognizes ``FIXME`` by default.
    """

    def __init__(self, **options):
        Filter.__init__(self, **options)
        tags = get_list_opt(options, 'codetags',
                            ['XXX', 'TODO', 'FIXME', 'BUG', 'NOTE'])
        self.tag_re = re.compile(r'\b({})\b'.format('|'.join([
            re.escape(tag) for tag in tags if tag
        ])))

    def filter(self, lexer, stream):
        regex = self.tag_re
        for ttype, value in stream:
            if ttype in String.Doc or \
               ttype in Comment and \
               ttype not in Comment.Preproc:
                yield from _replace_special(ttype, value, regex, Comment.Special)
            else:
                yield ttype, value


class SymbolFilter(Filter):
    """Convert mathematical symbols such as \\<longrightarrow> in Isabelle
    or \\longrightarrow in LaTeX into Unicode characters.

    This is mostly useful for HTML or console output when you want to
    approximate the source rendering you'd see in an IDE.

    Options accepted:

    `lang` : string
       The symbol language. Must be one of ``'isabelle'`` or
       ``'latex'``.  The default is ``'isabelle'``.
    """

    latex_symbols = {
        '\\alpha'                : '\U000003b1',
        '\\beta'                 : '\U000003b2',
        '\\gamma'                : '\U000003b3',
        '\\delta'                : '\U000003b4',
        '\\varepsilon'           : '\U000003b5',
        '\\zeta'                 : '\U000003b6',
        '\\eta'                  : '\U000003b7',
        '\\vartheta'             : '\U000003b8',
        '\\iota'                 : '\U000003b9',
        '\\kappa'                : '\U000003ba',
        '\\lambda'               : '\U000003bb',
        '\\mu'                   : '\U000003bc',
        '\\nu'                   : '\U000003bd',
        '\\xi'                   : '\U000003be',
        '\\pi'                   : '\U000003c0',
        '\\varrho'               : '\U000003c1',
        '\\sigma'                : '\U000003c3',
        '\\tau'                  : '\U000003c4',
        '\\upsilon'              : '\U000003c5',
        '\\varphi'               : '\U000003c6',
        '\\chi'                  : '\U000003c7',
        '\\psi'                  : '\U000003c8',
        '\\omega'                : '\U000003c9',
        '\\Gamma'                : '\U00000393',
        '\\Delta'                : '\U00000394',
        '\\Theta'                : '\U00000398',
        '\\Lambda'               : '\U0000039b',
        '\\Xi'                   : '\U0000039e',
        '\\Pi'                   : '\U000003a0',
        '\\Sigma'                : '\U000003a3',
        '\\Upsilon'              : '\U000003a5',
        '\\Phi'                  : '\U000003a6',
        '\\Psi'                  : '\U000003a8',
        '\\Omega'                : '\U000003a9',
        '\\leftarrow'            : '\U00002190',
        '\\longleftarrow'        : '\U000027f5',
        '\\rightarrow'           : '\U00002192',
        '\\longrightarrow'       : '\U000027f6',
        '\\Leftarrow'            : '\U000021d0',
        '\\Longleftarrow'        : '\U000027f8',
        '\\Rightarrow'           : '\U000021d2',
        '\\Longrightarrow'       : '\U000027f9',
        '\\leftrightarrow'       : '\U00002194',
        '\\longleftrightarrow'   : '\U000027f7',
        '\\Leftrightarrow'       : '\U000021d4',
        '\\Longleftrightarrow'   : '\U000027fa',
        '\\mapsto'               : '\U000021a6',
        '\\longmapsto'           : '\U000027fc',
        '\\relbar'               : '\U00002500',
        '\\Relbar'               : '\U00002550',
        '\\hookleftarrow'        : '\U000021a9',
        '\\hookrightarrow'       : '\U000021aa',
        '\\leftharpoondown'      : '\U000021bd',
        '\\rightharpoondown'     : '\U000021c1',
        '\\leftharpoonup'        : '\U000021bc',
        '\\rightharpoonup'       : '\U000021c0',
        '\\rightleftharpoons'    : '\U000021cc',
        '\\leadsto'              : '\U0000219d',
        '\\downharpoonleft'      : '\U000021c3',
        '\\downharpoonright'     : '\U000021c2',
        '\\upharpoonleft'        : '\U000021bf',
        '\\upharpoonright'       : '\U000021be',
        '\\restriction'          : '\U000021be',
        '\\uparrow'              : '\U00002191',
        '\\Uparrow'              : '\U000021d1',
        '\\downarrow'            : '\U00002193',
        '\\Downarrow'            : '\U000021d3',
        '\\updownarrow'          : '\U00002195',
        '\\Updownarrow'          : '\U000021d5',
        '\\langle'               : '\U000027e8',
        '\\rangle'               : '\U000027e9',
        '\\lceil'                : '\U00002308',
        '\\rceil'                : '\U00002309',
        '\\lfloor'               : '\U0000230a',
        '\\rfloor'               : '\U0000230b',
        '\\flqq'                 : '\U000000ab',
        '\\frqq'                 : '\U000000bb',
        '\\bot'                  : '\U000022a5',
        '\\top'                  : '\U000022a4',
        '\\wedge'                : '\U00002227',
        '\\bigwedge'             : '\U000022c0',
        '\\vee'                  : '\U00002228',
        '\\bigvee'               : '\U000022c1',
        '\\forall'               : '\U00002200',
        '\\exists'               : '\U00002203',
        '\\nexists'              : '\U00002204',
        '\\neg'                  : '\U000000ac',
        '\\Box'                  : '\U000025a1',
        '\\Diamond'              : '\U000025c7',
        '\\vdash'                : '\U000022a2',
        '\\models'               : '\U000022a8',
        '\\dashv'                : '\U000022a3',
        '\\surd'                 : '\U0000221a',
        '\\le'                   : '\U00002264',
        '\\ge'                   : '\U00002265',
        '\\ll'                   : '\U0000226a',
        '\\gg'                   : '\U0000226b',
        '\\lesssim'              : '\U00002272',
        '\\gtrsim'               : '\U00002273',
        '\\lessapprox'           : '\U00002a85',
        '\\gtrapprox'            : '\U00002a86',
        '\\in'                   : '\U00002208',
        '\\notin'                : '\U00002209',
        '\\subset'               : '\U00002282',
        '\\supset'               : '\U00002283',
        '\\subseteq'             : '\U00002286',
        '\\supseteq'             : '\U00002287',
        '\\sqsubset'             : '\U0000228f',
        '\\sqsupset'             : '\U00002290',
        '\\sqsubseteq'           : '\U00002291',
        '\\sqsupseteq'           : '\U00002292',
        '\\cap'                  : '\U00002229',
        '\\bigcap'               : '\U000022c2',
        '\\cup'                  : '\U0000222a',
        '\\bigcup'               : '\U000022c3',
        '\\sqcup'                : '\U00002294',
        '\\bigsqcup'             : '\U00002a06',
        '\\sqcap'                : '\U00002293',
        '\\Bigsqcap'             : '\U00002a05',
        '\\setminus'             : '\U00002216',
        '\\propto'               : '\U0000221d',
        '\\uplus'                : '\U0000228e',
        '\\bigplus'              : '\U00002a04',
        '\\sim'                  : '\U0000223c',
        '\\doteq'                : '\U00002250',
        '\\simeq'                : '\U00002243',
        '\\approx'               : '\U00002248',
        '\\asymp'                : '\U0000224d',
        '\\cong'                 : '\U00002245',
        '\\equiv'                : '\U00002261',
        '\\Join'                 : '\U000022c8',
        '\\bowtie'               : '\U00002a1d',
        '\\prec'                 : '\U0000227a',
        '\\succ'                 : '\U0000227b',
        '\\preceq'               : '\U0000227c',
        '\\succeq'               : '\U0000227d',
        '\\parallel'             : '\U00002225',
        '\\mid'                  : '\U000000a6',
        '\\pm'                   : '\U000000b1',
        '\\mp'                   : '\U00002213',
        '\\times'                : '\U000000d7',
        '\\div'                  : '\U000000f7',
        '\\cdot'                 : '\U000022c5',
        '\\star'                 : '\U000022c6',
        '\\circ'                 : '\U00002218',
        '\\dagger'               : '\U00002020',
        '\\ddagger'              : '\U00002021',
        '\\lhd'                  : '\U000022b2',
        '\\rhd'                  : '\U000022b3',
        '\\unlhd'                : '\U000022b4',
        '\\unrhd'                : '\U000022b5',
        '\\triangleleft'         : '\U000025c3',
        '\\triangleright'        : '\U000025b9',
        '\\triangle'             : '\U000025b3',
        '\\triangleq'            : '\U0000225c',
        '\\oplus'                : '\U00002295',
        '\\bigoplus'             : '\U00002a01',
        '\\otimes'               : '\U00002297',
        '\\bigotimes'            : '\U00002a02',
        '\\odot'                 : '\U00002299',
        '\\bigodot'              : '\U00002a00',
        '\\ominus'               : '\U00002296',
        '\\oslash'               : '\U00002298',
        '\\dots'                 : '\U00002026',
        '\\cdots'                : '\U000022ef',
        '\\sum'                  : '\U00002211',
        '\\prod'                 : '\U0000220f',
        '\\coprod'               : '\U00002210',
        '\\infty'                : '\U0000221e',
        '\\int'                  : '\U0000222b',
        '\\oint'                 : '\U0000222e',
        '\\clubsuit'             : '\U00002663',
        '\\diamondsuit'          : '\U00002662',
        '\\heartsuit'            : '\U00002661',
        '\\spadesuit'            : '\U00002660',
        '\\aleph'                : '\U00002135',
        '\\emptyset'             : '\U00002205',
        '\\nabla'                : '\U00002207',
        '\\partial'              : '\U00002202',
        '\\flat'                 : '\U0000266d',
        '\\natural'              : '\U0000266e',
        '\\sharp'                : '\U0000266f',
        '\\angle'                : '\U00002220',
        '\\copyright'            : '\U000000a9',
        '\\textregistered'       : '\U000000ae',
        '\\textonequarter'       : '\U000000bc',
        '\\textonehalf'          : '\U000000bd',
        '\\textthreequarters'    : '\U000000be',
        '\\textordfeminine'      : '\U000000aa',
        '\\textordmasculine'     : '\U000000ba',
        '\\euro'                 : '\U000020ac',
        '\\pounds'               : '\U000000a3',
        '\\yen'                  : '\U000000a5',
        '\\textcent'             : '\U000000a2',
        '\\textcurrency'         : '\U000000a4',
        '\\textdegree'           : '\U000000b0',
    }

    isabelle_symbols = {
        '\\<zero>'                 : '\U0001d7ec',
        '\\<one>'                  : '\U0001d7ed',
        '\\<two>'                  : '\U0001d7ee',
        '\\<three>'                : '\U0001d7ef',
        '\\<four>'                 : '\U0001d7f0',
        '\\<five>'                 : '\U0001d7f1',
        '\\<six>'                  : '\U0001d7f2',
        '\\<seven>'                : '\U0001d7f3',
        '\\<eight>'                : '\U0001d7f4',
        '\\<nine>'                 : '\U0001d7f5',
        '\\<A>'                    : '\U0001d49c',
        '\\<B>'                    : '\U0000212c',
        '\\<C>'                    : '\U0001d49e',
        '\\<D>'                    : '\U0001d49f',
        '\\<E>'                    : '\U00002130',
        '\\<F>'                    : '\U00002131',
        '\\<G>'                    : '\U0001d4a2',
        '\\<H>'                    : '\U0000210b',
        '\\<I>'                    : '\U00002110',
        '\\<J>'                    : '\U0001d4a5',
        '\\<K>'                    : '\U0001d4a6',
        '\\<L>'                    : '\U00002112',
        '\\<M>'                    : '\U00002133',
        '\\<N>'                    : '\U0001d4a9',
        '\\<O>'                    : '\U0001d4aa',
        '\\<P>'                    : '\U0001d4ab',
        '\\<Q>'                    : '\U0001d4ac',
        '\\<R>'                    : '\U0000211b',
        '\\<S>'                    : '\U0001d4ae',
        '\\<T>'                    : '\U0001d4af',
        '\\<U>'                    : '\U0001d4b0',
        '\\<V>'                    : '\U0001d4b1',
        '\\<W>'                    : '\U0001d4b2',
        '\\<X>'                    : '\U0001d4b3',
        '\\<Y>'                    : '\U0001d4b4',
        '\\<Z>'                    : '\U0001d4b5',
        '\\<a>'                    : '\U0001d5ba',
        '\\<b>'                    : '\U0001d5bb',
        '\\<c>'                    : '\U0001d5bc',
        '\\<d>'                    : '\U0001d5bd',
        '\\<e>'                    : '\U0001d5be',
        '\\<f>'                    : '\U0001d5bf',
        '\\<g>'                    : '\U0001d5c0',
        '\\<h>'                    : '\U0001d5c1',
        '\\<i>'                    : '\U0001d5c2',
        '\\<j>'                    : '\U0001d5c3',
        '\\<k>'                    : '\U0001d5c4',
        '\\<l>'                    : '\U0001d5c5',
        '\\<m>'                    : '\U0001d5c6',
        '\\<n>'                    : '\U0001d5c7',
        '\\<o>'                    : '\U0001d5c8',
        '\\<p>'                    : '\U0001d5c9',
        '\\<q>'                    : '\U0001d5ca',
        '\\<r>'                    : '\U0001d5cb',
        '\\<s>'                    : '\U0001d5cc',
        '\\<t>'                    : '\U0001d5cd',
        '\\<u>'                    : '\U0001d5ce',
        '\\<v>'                    : '\U0001d5cf',
        '\\<w>'                    : '\U0001d5d0',
        '\\<x>'                    : '\U0001d5d1',
        '\\<y>'                    : '\U0001d5d2',
        '\\<z>'                    : '\U0001d5d3',
        '\\<AA>'                   : '\U0001d504',
        '\\<BB>'                   : '\U0001d505',
        '\\<CC>'                   : '\U0000212d',
        '\\<DD>'                   : '\U0001d507',
        '\\<EE>'                   : '\U0001d508',
        '\\<FF>'                   : '\U0001d509',
        '\\<GG>'                   : '\U0001d50a',
        '\\<HH>'                   : '\U0000210c',
        '\\<II>'                   : '\U00002111',
        '\\<JJ>'                   : '\U0001d50d',
        '\\<KK>'                   : '\U0001d50e',
        '\\<LL>'                   : '\U0001d50f',
        '\\<MM>'                   : '\U0001d510',
        '\\<NN>'                   : '\U0001d511',
        '\\<OO>'                   : '\U0001d512',
        '\\<PP>'                   : '\U0001d513',
        '\\<QQ>'                   : '\U0001d514',
        '\\<RR>'                   : '\U0000211c',
        '\\<SS>'                   : '\U0001d516',
        '\\<TT>'                   : '\U0001d517',
        '\\<UU>'                   : '\U0001d518',
        '\\<VV>'                   : '\U0001d519',
        '\\<WW>'                   : '\U0001d51a',
        '\\<XX>'                   : '\U0001d51b',
        '\\<YY>'                   : '\U0001d51c',
        '\\<ZZ>'                   : '\U00002128',
        '\\<aa>'                   : '\U0001d51e',
        '\\<bb>'                   : '\U0001d51f',
        '\\<cc>'                   : '\U0001d520',
        '\\<dd>'                   : '\U0001d521',
        '\\<ee>'                   : '\U0001d522',
        '\\<ff>'                   : '\U0001d523',
        '\\<gg>'                   : '\U0001d524',
        '\\<hh>'                   : '\U0001d525',
        '\\<ii>'                   : '\U0001d526',
        '\\<jj>'                   : '\U0001d527',
        '\\<kk>'                   : '\U0001d528',
        '\\<ll>'                   : '\U0001d529',
        '\\<mm>'                   : '\U0001d52a',
        '\\<nn>'                   : '\U0001d52b',
        '\\<oo>'                   : '\U0001d52c',
        '\\<pp>'                   : '\U0001d52d',
        '\\<qq>'                   : '\U0001d52e',
        '\\<rr>'                   : '\U0001d52f',
        '\\<ss>'                   : '\U0001d530',
        '\\<tt>'                   : '\U0001d531',
        '\\<uu>'                   : '\U0001d532',
        '\\<vv>'                   : '\U0001d533',
        '\\<ww>'                   : '\U0001d534',
        '\\<xx>'                   : '\U0001d535',
        '\\<yy>'                   : '\U0001d536',
        '\\<zz>'                   : '\U0001d537',
        '\\<alpha>'                : '\U000003b1',
        '\\<beta>'                 : '\U000003b2',
        '\\<gamma>'                : '\U000003b3',
        '\\<delta>'                : '\U000003b4',
        '\\<epsilon>'              : '\U000003b5',
        '\\<zeta>'                 : '\U000003b6',
        '\\<eta>'                  : '\U000003b7',
        '\\<theta>'                : '\U000003b8',
        '\\<iota>'                 : '\U000003b9',
        '\\<kappa>'                : '\U000003ba',
        '\\<lambda>'               : '\U000003bb',
        '\\<mu>'                   : '\U000003bc',
        '\\<nu>'                   : '\U000003bd',
        '\\<xi>'                   : '\U000003be',
        '\\<pi>'                   : '\U000003c0',
        '\\<rho>'                  : '\U000003c1',
        '\\<sigma>'                : '\U000003c3',
        '\\<tau>'                  : '\U000003c4',
        '\\<upsilon>'              : '\U000003c5',
        '\\<phi>'                  : '\U000003c6',
        '\\<chi>'                  : '\U000003c7',
        '\\<psi>'                  : '\U000003c8',
        '\\<omega>'                : '\U000003c9',
        '\\<Gamma>'                : '\U00000393',
        '\\<Delta>'                : '\U00000394',
        '\\<Theta>'                : '\U00000398',
        '\\<Lambda>'               : '\U0000039b',
        '\\<Xi>'                   : '\U0000039e',
        '\\<Pi>'                   : '\U000003a0',
        '\\<Sigma>'                : '\U000003a3',
        '\\<Upsilon>'              : '\U000003a5',
        '\\<Phi>'                  : '\U000003a6',
        '\\<Psi>'                  : '\U000003a8',
        '\\<Omega>'                : '\U000003a9',
        '\\<bool>'                 : '\U0001d539',
        '\\<complex>'              : '\U00002102',
        '\\<nat>'                  : '\U00002115',
        '\\<rat>'                  : '\U0000211a',
        '\\<real>'                 : '\U0000211d',
        '\\<int>'                  : '\U00002124',
        '\\<leftarrow>'            : '\U00002190',
        '\\<longleftarrow>'        : '\U000027f5',
        '\\<rightarrow>'           : '\U00002192',
        '\\<longrightarrow>'       : '\U000027f6',
        '\\<Leftarrow>'            : '\U000021d0',
        '\\<Longleftarrow>'        : '\U000027f8',
        '\\<Rightarrow>'           : '\U000021d2',
        '\\<Longrightarrow>'       : '\U000027f9',
        '\\<leftrightarrow>'       : '\U00002194',
        '\\<longleftrightarrow>'   : '\U000027f7',
        '\\<Leftrightarrow>'       : '\U000021d4',
        '\\<Longleftrightarrow>'   : '\U000027fa',
        '\\<mapsto>'               : '\U000021a6',
        '\\<longmapsto>'           : '\U000027fc',
        '\\<midarrow>'             : '\U00002500',
        '\\<Midarrow>'             : '\U00002550',
        '\\<hookleftarrow>'        : '\U000021a9',
        '\\<hookrightarrow>'       : '\U000021aa',
        '\\<leftharpoondown>'      : '\U000021bd',
        '\\<rightharpoondown>'     : '\U000021c1',
        '\\<leftharpoonup>'        : '\U000021bc',
        '\\<rightharpoonup>'       : '\U000021c0',
        '\\<rightleftharpoons>'    : '\U000021cc',
        '\\<leadsto>'              : '\U0000219d',
        '\\<downharpoonleft>'      : '\U000021c3',
        '\\<downharpoonright>'     : '\U000021c2',
        '\\<upharpoonleft>'        : '\U000021bf',
        '\\<upharpoonright>'       : '\U000021be',
        '\\<restriction>'          : '\U000021be',
        '\\<Colon>'                : '\U00002237',
        '\\<up>'                   : '\U00002191',
        '\\<Up>'                   : '\U000021d1',
        '\\<down>'                 : '\U00002193',
        '\\<Down>'                 : '\U000021d3',
        '\\<updown>'               : '\U00002195',
        '\\<Updown>'               : '\U000021d5',
        '\\<langle>'               : '\U000027e8',
        '\\<rangle>'               : '\U000027e9',
        '\\<lceil>'                : '\U00002308',
        '\\<rceil>'                : '\U00002309',
        '\\<lfloor>'               : '\U0000230a',
        '\\<rfloor>'               : '\U0000230b',
        '\\<lparr>'                : '\U00002987',
        '\\<rparr>'                : '\U00002988',
        '\\<lbrakk>'               : '\U000027e6',
        '\\<rbrakk>'               : '\U000027e7',
        '\\<lbrace>'               : '\U00002983',
        '\\<rbrace>'               : '\U00002984',
        '\\<guillemotleft>'        : '\U000000ab',
        '\\<guillemotright>'       : '\U000000bb',
        '\\<bottom>'               : '\U000022a5',
        '\\<top>'                  : '\U000022a4',
        '\\<and>'                  : '\U00002227',
        '\\<And>'                  : '\U000022c0',
        '\\<or>'                   : '\U00002228',
        '\\<Or>'                   : '\U000022c1',
        '\\<forall>'               : '\U00002200',
        '\\<exists>'               : '\U00002203',
        '\\<nexists>'              : '\U00002204',
        '\\<not>'                  : '\U000000ac',
        '\\<box>'                  : '\U000025a1',
        '\\<diamond>'              : '\U000025c7',
        '\\<turnstile>'            : '\U000022a2',
        '\\<Turnstile>'            : '\U000022a8',
        '\\<tturnstile>'           : '\U000022a9',
        '\\<TTurnstile>'           : '\U000022ab',
        '\\<stileturn>'            : '\U000022a3',
        '\\<surd>'                 : '\U0000221a',
        '\\<le>'                   : '\U00002264',
        '\\<ge>'                   : '\U00002265',
        '\\<lless>'                : '\U0000226a',
        '\\<ggreater>'             : '\U0000226b',
        '\\<lesssim>'              : '\U00002272',
        '\\<greatersim>'           : '\U00002273',
        '\\<lessapprox>'           : '\U00002a85',
        '\\<greaterapprox>'        : '\U00002a86',
        '\\<in>'                   : '\U00002208',
        '\\<notin>'                : '\U00002209',
        '\\<subset>'               : '\U00002282',
        '\\<supset>'               : '\U00002283',
        '\\<subseteq>'             : '\U00002286',
        '\\<supseteq>'             : '\U00002287',
        '\\<sqsubset>'             : '\U0000228f',
        '\\<sqsupset>'             : '\U00002290',
        '\\<sqsubseteq>'           : '\U00002291',
        '\\<sqsupseteq>'           : '\U00002292',
        '\\<inter>'                : '\U00002229',
        '\\<Inter>'                : '\U000022c2',
        '\\<union>'                : '\U0000222a',
        '\\<Union>'                : '\U000022c3',
        '\\<squnion>'              : '\U00002294',
        '\\<Squnion>'              : '\U00002a06',
        '\\<sqinter>'              : '\U00002293',
        '\\<Sqinter>'              : '\U00002a05',
        '\\<setminus>'             : '\U00002216',
        '\\<propto>'               : '\U0000221d',
        '\\<uplus>'                : '\U0000228e',
        '\\<Uplus>'                : '\U00002a04',
        '\\<noteq>'                : '\U00002260',
        '\\<sim>'                  : '\U0000223c',
        '\\<doteq>'                : '\U00002250',
        '\\<simeq>'                : '\U00002243',
        '\\<approx>'               : '\U00002248',
        '\\<asymp>'                : '\U0000224d',
        '\\<cong>'                 : '\U00002245',
        '\\<smile>'                : '\U00002323',
        '\\<equiv>'                : '\U00002261',
        '\\<frown>'                : '\U00002322',
        '\\<Join>'                 : '\U000022c8',
        '\\<bowtie>'               : '\U00002a1d',
        '\\<prec>'                 : '\U0000227a',
        '\\<succ>'                 : '\U0000227b',
        '\\<preceq>'               : '\U0000227c',
        '\\<succeq>'               : '\U0000227d',
        '\\<parallel>'             : '\U00002225',
        '\\<bar>'                  : '\U000000a6',
        '\\<plusminus>'            : '\U000000b1',
        '\\<minusplus>'            : '\U00002213',
        '\\<times>'                : '\U000000d7',
        '\\<div>'                  : '\U000000f7',
        '\\<cdot>'                 : '\U000022c5',
        '\\<star>'                 : '\U000022c6',
        '\\<bullet>'               : '\U00002219',
        '\\<circ>'                 : '\U00002218',
        '\\<dagger>'               : '\U00002020',
        '\\<ddagger>'              : '\U00002021',
        '\\<lhd>'                  : '\U000022b2',
        '\\<rhd>'                  : '\U000022b3',
        '\\<unlhd>'                : '\U000022b4',
        '\\<unrhd>'                : '\U000022b5',
        '\\<triangleleft>'         : '\U000025c3',
        '\\<triangleright>'        : '\U000025b9',
        '\\<triangle>'             : '\U000025b3',
        '\\<triangleq>'            : '\U0000225c',
        '\\<oplus>'                : '\U00002295',
        '\\<Oplus>'                : '\U00002a01',
        '\\<otimes>'               : '\U00002297',
        '\\<Otimes>'               : '\U00002a02',
        '\\<odot>'                 : '\U00002299',
        '\\<Odot>'                 : '\U00002a00',
        '\\<ominus>'               : '\U00002296',
        '\\<oslash>'               : '\U00002298',
        '\\<dots>'                 : '\U00002026',
        '\\<cdots>'                : '\U000022ef',
        '\\<Sum>'                  : '\U00002211',
        '\\<Prod>'                 : '\U0000220f',
        '\\<Coprod>'               : '\U00002210',
        '\\<infinity>'             : '\U0000221e',
        '\\<integral>'             : '\U0000222b',
        '\\<ointegral>'            : '\U0000222e',
        '\\<clubsuit>'             : '\U00002663',
        '\\<diamondsuit>'          : '\U00002662',
        '\\<heartsuit>'            : '\U00002661',
        '\\<spadesuit>'            : '\U00002660',
        '\\<aleph>'                : '\U00002135',
        '\\<emptyset>'             : '\U00002205',
        '\\<nabla>'                : '\U00002207',
        '\\<partial>'              : '\U00002202',
        '\\<flat>'                 : '\U0000266d',
        '\\<natural>'              : '\U0000266e',
        '\\<sharp>'                : '\U0000266f',
        '\\<angle>'                : '\U00002220',
        '\\<copyright>'            : '\U000000a9',
        '\\<registered>'           : '\U000000ae',
        '\\<hyphen>'               : '\U000000ad',
        '\\<inverse>'              : '\U000000af',
        '\\<onequarter>'           : '\U000000bc',
        '\\<onehalf>'              : '\U000000bd',
        '\\<threequarters>'        : '\U000000be',
        '\\<ordfeminine>'          : '\U000000aa',
        '\\<ordmasculine>'         : '\U000000ba',
        '\\<section>'              : '\U000000a7',
        '\\<paragraph>'            : '\U000000b6',
        '\\<exclamdown>'           : '\U000000a1',
        '\\<questiondown>'         : '\U000000bf',
        '\\<euro>'                 : '\U000020ac',
        '\\<pounds>'               : '\U000000a3',
        '\\<yen>'                  : '\U000000a5',
        '\\<cent>'                 : '\U000000a2',
        '\\<currency>'             : '\U000000a4',
        '\\<degree>'               : '\U000000b0',
        '\\<amalg>'                : '\U00002a3f',
        '\\<mho>'                  : '\U00002127',
        '\\<lozenge>'              : '\U000025ca',
        '\\<wp>'                   : '\U00002118',
        '\\<wrong>'                : '\U00002240',
        '\\<struct>'               : '\U000022c4',
        '\\<acute>'                : '\U000000b4',
        '\\<index>'                : '\U00000131',
        '\\<dieresis>'             : '\U000000a8',
        '\\<cedilla>'              : '\U000000b8',
        '\\<hungarumlaut>'         : '\U000002dd',
        '\\<some>'                 : '\U000003f5',
        '\\<newline>'              : '\U000023ce',
        '\\<open>'                 : '\U00002039',
        '\\<close>'                : '\U0000203a',
        '\\<here>'                 : '\U00002302',
        '\\<^sub>'                 : '\U000021e9',
        '\\<^sup>'                 : '\U000021e7',
        '\\<^bold>'                : '\U00002759',
        '\\<^bsub>'                : '\U000021d8',
        '\\<^esub>'                : '\U000021d9',
        '\\<^bsup>'                : '\U000021d7',
        '\\<^esup>'                : '\U000021d6',
    }

    lang_map = {'isabelle' : isabelle_symbols, 'latex' : latex_symbols}

    def __init__(self, **options):
        Filter.__init__(self, **options)
        lang = get_choice_opt(options, 'lang',
                              ['isabelle', 'latex'], 'isabelle')
        self.symbols = self.lang_map[lang]

    def filter(self, lexer, stream):
        for ttype, value in stream:
            if value in self.symbols:
                yield ttype, self.symbols[value]
            else:
                yield ttype, value


class KeywordCaseFilter(Filter):
    """Convert keywords to lowercase or uppercase or capitalize them, which
    means first letter uppercase, rest lowercase.

    This can be useful e.g. if you highlight Pascal code and want to adapt the
    code to your styleguide.

    Options accepted:

    `case` : string
       The casing to convert keywords to. Must be one of ``'lower'``,
       ``'upper'`` or ``'capitalize'``.  The default is ``'lower'``.
    """

    def __init__(self, **options):
        Filter.__init__(self, **options)
        case = get_choice_opt(options, 'case',
                              ['lower', 'upper', 'capitalize'], 'lower')
        self.convert = getattr(str, case)

    def filter(self, lexer, stream):
        for ttype, value in stream:
            if ttype in Keyword:
                yield ttype, self.convert(value)
            else:
                yield ttype, value


class NameHighlightFilter(Filter):
    """Highlight a normal Name (and Name.*) token with a different token type.

    Example::

        filter = NameHighlightFilter(
            names=['foo', 'bar', 'baz'],
            tokentype=Name.Function,
        )

    This would highlight the names "foo", "bar" and "baz"
    as functions. `Name.Function` is the default token type.

    Options accepted:

    `names` : list of strings
      A list of names that should be given the different token type.
      There is no default.
    `tokentype` : TokenType or string
      A token type or a string containing a token type name that is
      used for highlighting the strings in `names`.  The default is
      `Name.Function`.
    """

    def __init__(self, **options):
        Filter.__init__(self, **options)
        self.names = set(get_list_opt(options, 'names', []))
        tokentype = options.get('tokentype')
        if tokentype:
            self.tokentype = string_to_tokentype(tokentype)
        else:
            self.tokentype = Name.Function

    def filter(self, lexer, stream):
        for ttype, value in stream:
            if ttype in Name and value in self.names:
                yield self.tokentype, value
            else:
                yield ttype, value


class ErrorToken(Exception):
    pass


class RaiseOnErrorTokenFilter(Filter):
    """Raise an exception when the lexer generates an error token.

    Options accepted:

    `excclass` : Exception class
      The exception class to raise.
      The default is `pygments.filters.ErrorToken`.

    .. versionadded:: 0.8
    """

    def __init__(self, **options):
        Filter.__init__(self, **options)
        self.exception = options.get('excclass', ErrorToken)
        try:
            # issubclass() will raise TypeError if first argument is not a class
            if not issubclass(self.exception, Exception):
                raise TypeError
        except TypeError:
            raise OptionError('excclass option is not an exception class')

    def filter(self, lexer, stream):
        for ttype, value in stream:
            if ttype is Error:
                raise self.exception(value)
            yield ttype, value


class VisibleWhitespaceFilter(Filter):
    """Convert tabs, newlines and/or spaces to visible characters.

    Options accepted:

    `spaces` : string or bool
      If this is a one-character string, spaces will be replaces by this string.
      If it is another true value, spaces will be replaced by ``·`` (unicode
      MIDDLE DOT).  If it is a false value, spaces will not be replaced.  The
      default is ``False``.
    `tabs` : string or bool
      The same as for `spaces`, but the default replacement character is ``»``
      (unicode RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK).  The default value
      is ``False``.  Note: this will not work if the `tabsize` option for the
      lexer is nonzero, as tabs will already have been expanded then.
    `tabsize` : int
      If tabs are to be replaced by this filter (see the `tabs` option), this
      is the total number of characters that a tab should be expanded to.
      The default is ``8``.
    `newlines` : string or bool
      The same as for `spaces`, but the default replacement character is ``¶``
      (unicode PILCROW SIGN).  The default value is ``False``.
    `wstokentype` : bool
      If true, give whitespace the special `Whitespace` token type.  This allows
      styling the visible whitespace differently (e.g. greyed out), but it can
      disrupt background colors.  The default is ``True``.

    .. versionadded:: 0.8
    """

    def __init__(self, **options):
        Filter.__init__(self, **options)
        for name, default in [('spaces',   '·'),
                              ('tabs',     '»'),
                              ('newlines', '¶')]:
            opt = options.get(name, False)
            if isinstance(opt, str) and len(opt) == 1:
                setattr(self, name, opt)
            else:
                setattr(self, name, (opt and default or ''))
        tabsize = get_int_opt(options, 'tabsize', 8)
        if self.tabs:
            self.tabs += ' ' * (tabsize - 1)
        if self.newlines:
            self.newlines += '\n'
        self.wstt = get_bool_opt(options, 'wstokentype', True)

    def filter(self, lexer, stream):
        if self.wstt:
            spaces = self.spaces or ' '
            tabs = self.tabs or '\t'
            newlines = self.newlines or '\n'
            regex = re.compile(r'\s')

            def replacefunc(wschar):
                if wschar == ' ':
                    return spaces
                elif wschar == '\t':
                    return tabs
                elif wschar == '\n':
                    return newlines
                return wschar

            for ttype, value in stream:
                yield from _replace_special(ttype, value, regex, Whitespace,
                                            replacefunc)
        else:
            spaces, tabs, newlines = self.spaces, self.tabs, self.newlines
            # simpler processing
            for ttype, value in stream:
                if spaces:
                    value = value.replace(' ', spaces)
                if tabs:
                    value = value.replace('\t', tabs)
                if newlines:
                    value = value.replace('\n', newlines)
                yield ttype, value


class GobbleFilter(Filter):
    """Gobbles source code lines (eats initial characters).

    This filter drops the first ``n`` characters off every line of code.  This
    may be useful when the source code fed to the lexer is indented by a fixed
    amount of space that isn't desired in the output.

    Options accepted:

    `n` : int
       The number of characters to gobble.

    .. versionadded:: 1.2
    """
    def __init__(self, **options):
        Filter.__init__(self, **options)
        self.n = get_int_opt(options, 'n', 0)

    def gobble(self, value, left):
        if left < len(value):
            return value[left:], 0
        else:
            return '', left - len(value)

    def filter(self, lexer, stream):
        n = self.n
        left = n  # How many characters left to gobble.
        for ttype, value in stream:
            # Remove ``left`` tokens from first line, ``n`` from all others.
            parts = value.split('\n')
            (parts[0], left) = self.gobble(parts[0], left)
            for i in range(1, len(parts)):
                (parts[i], left) = self.gobble(parts[i], n)
            value = '\n'.join(parts)

            if value != '':
                yield ttype, value


class TokenMergeFilter(Filter):
    """Merges consecutive tokens with the same token type in the output
    stream of a lexer.

    .. versionadded:: 1.2
    """
    def __init__(self, **options):
        Filter.__init__(self, **options)

    def filter(self, lexer, stream):
        current_type = None
        current_value = None
        for ttype, value in stream:
            if ttype is current_type:
                current_value += value
            else:
                if current_type is not None:
                    yield current_type, current_value
                current_type = ttype
                current_value = value
        if current_type is not None:
            yield current_type, current_value


FILTERS = {
    'codetagify':     CodeTagFilter,
    'keywordcase':    KeywordCaseFilter,
    'highlight':      NameHighlightFilter,
    'raiseonerror':   RaiseOnErrorTokenFilter,
    'whitespace':     VisibleWhitespaceFilter,
    'gobble':         GobbleFilter,
    'tokenmerge':     TokenMergeFilter,
    'symbols':        SymbolFilter,
}
