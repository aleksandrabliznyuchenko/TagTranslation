# import re
import spacy
from spacy.tokenizer import Tokenizer
# from spacy.lang.en import English
from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER, HYPHENS, CURRENCY, UNITS, PUNCT
from spacy.lang.char_classes import CONCAT_QUOTES, LIST_ELLIPSES, LIST_ICONS, LIST_PUNCT, LIST_QUOTES
from spacy.util import compile_infix_regex


# special_cases = {":)": [{"ORTH": ":)"}]}
# prefix_re = re.compile(r'''^[\[\("']''')
# suffix_re = re.compile(r'''[\]\)"']$''')
# infix_re = re.compile(r'''[-~]''')
# simple_url_re = re.compile(r'''^https?://''')

"""
In many situations, you don’t necessarily need entirely custom rules. 
Sometimes you just want to add another character to the prefixes, suffixes or infixes. 
The default prefix, suffix and infix rules are available via the nlp object’s Defaults 
and the Tokenizer attributes such as Tokenizer.suffix_search
"""
# suffixes = nlp.Defaults.suffixes + [r'''-+$''',]
# suffix_regex = spacy.util.compile_suffix_regex(suffixes)
# nlp.tokenizer.suffix_search = suffix_regex.search

# Similarly, you can remove a character from the default suffixes:
# suffixes = list(nlp.Defaults.suffixes)
# suffixes.remove("\\[")
# suffix_regex = spacy.util.compile_suffix_regex(suffixes)
# nlp.tokenizer.suffix_search = suffix_regex.search


def custom_tokenizer(nlp):
    # special_cases = {"cannot": [{"ORTH": "can"}, {"ORTH": "not"}]}

    # modify tokenizer infix patterns
    infixes = (
            LIST_ELLIPSES
            + LIST_ICONS
            + [
                # EDIT: commented out regex that splits on hyphens between digits:
                # r"(?<=[0-9])[+\-\*^](?=[0-9-])",
                # split 13(19  women(70%
                r"(?<=[0-9])[(%+\*^](?=[0-9-])",
                r"(?<=[{al}{q}])\.(?=[{au}{q}])".format(al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES),
                # split  "interest"-reason (two lines
                r"(?<=[{q}])-(?=[{al}])".format(al=ALPHA_LOWER, q=CONCAT_QUOTES),
                r"(?<=[{a}])\"(?=[-{a}])".format(a=ALPHA),
                # split diploma(about  women(70%
                r'(?<=[{a}])[(:<>=](?=[{a}0-9])'.format(a=ALPHA),
                # split 2012 too):
                # r'(?<=[)]):(?=[{a}0-9])'.format(a=ALPHA),

                r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
                # EDIT: commented out regex that splits on hyphens between letters:
                # r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
                # EDIT: add regex that splits on hyphens between % and digit:
                r"(?<=[%])(?:{h})(?=[0-9])".format(h=HYPHENS),
                # EDIT: add regex that splits on hyphens between " and alpha:
                # r"(?<=[{q}])(?:{h})(?=[{a})".format(q=CONCAT_QUOTES, h=HYPHENS, a=ALPHA),
                # EDIT: add regex that splits on colon between " and alpha:
                r"(?<=[{al}]):(?=[{q}])".format(al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES),
                # EDIT: commented out regex that splits on colon between letters/digits and letters:
                # r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
                r"(?<=[{a}0-9%])[:<>=/](?=[{a}0-9])".format(a=ALPHA),
                # make 70%/60% split
                r"(?<=[{a}0-9])[%](?=[/{a}0-9])".format(a=ALPHA),
                r"(?<=[{a}0-9])[<>=/](?=[-{a}])".format(a=ALPHA),
                r"(?<=[{a}])/(?=[{a}])".format(a=ALPHA),
            ]
    )

    infix_re = compile_infix_regex(infixes)
    # nlp.tokenizer.infix_finditer = infix_re.finditer

    # modify tokenizer suffix patterns
    # suffixes = list(nlp.Defaults.suffixes)

    suffixes = (
            LIST_PUNCT
            + LIST_ELLIPSES
            + LIST_QUOTES
            + LIST_ICONS
            + ["'s", "'S", "’s", "’S", "—", "–"]
            + [
                # do not split 60+
                # r"(?<=[0-9])\+",
                r"(?<=[0-9])%",
                r"(?<=°[FfCcKk])\.",
                r"(?<=[0-9])(?:{c})".format(c=CURRENCY),
                r"(?<=[0-9])(?:{u})".format(u=UNITS),
                r"(?<=[0-9{al}{e}{p}(?:{q})])\.".format(al=ALPHA_LOWER, e=r"%²\-\+", q=CONCAT_QUOTES, p=PUNCT),
                r"(?<=[{au}][{au}])\.".format(au=ALPHA_UPPER),
            ]
    )

    suffixes = suffixes + [r'''/'''] # split on '/'

    suffix_re = spacy.util.compile_suffix_regex(suffixes)
    # nlp.tokenizer.suffix_search = suffix_regex.search

    # modify tokenizer prefix patterns
    prefixes = list(nlp.Defaults.prefixes)
    prefixes = prefixes + [r'''/'''] + [r'''~''']  + [r''':''']# split on '/' and '~'
    # prefixes = nlp.Defaults.prefixes + (r'''/''',)          # split on '/'
    prefix_re = spacy.util.compile_prefix_regex(prefixes)
    # nlp.tokenizer.prefix_search = prefix_regex.search

    # return Tokenizer(nlp.vocab)
    return Tokenizer(nlp.vocab,
                     rules=nlp.Defaults.tokenizer_exceptions,
                     prefix_search=prefix_re.search,
                     suffix_search=suffix_re.search,
                     infix_finditer=infix_re.finditer,
                     # url_match=simple_url_re.match,
                     )


# print(nlp.tokenizer.explain(':'))
