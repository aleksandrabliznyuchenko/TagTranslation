from rules_base import RulesBase

"""
    We broaden error span and correction span. It is important to remember that we form the error span step by step.
    For example, for the error "a number" - "the percentage" we have to form 2 separate lines in the annotation file
    1. a number - the number (Articles)
    2. number - percentage (Choice of lexical item)

    Thus, it is our main goal to construct a correct broad error span - the correction will be later derived from it.
"""


class ErrorSpan(RulesBase):

    def __init__(self):
        super().__init__()

    def parameters(self, construction_dict, correction_dict, full_correction_dict,
                   error_token, token_id, sentence_tokens):
        self.construction_dict = construction_dict
        self.correction = correction_dict
        self.full_correction = full_correction_dict
        self.error_properties = error_token
        self.current_token_id = token_id
        self.sentence_tokens = sentence_tokens

    """
    Check whether token exists in the error span or correction
    """

    def match_error_token(self, corr_token, token_id, mode):
        key = None
        if len(self.construction_dict.keys()) >= token_id + 1:
            key = list(self.construction_dict.keys())[token_id]

        # POS-tag: 'number' - 'number' / 'member' / 'amounts'
        if mode == 1:
            if key and self.construction_dict[key]['token_pos'] == corr_token['token_pos']:
                return key, self.construction_dict[key]
            for token_id, error_token in self.construction_dict.items():
                if error_token['token_pos'] == corr_token['token_pos']:
                    return token_id, error_token

        # POS-tag + TreeTagger tag: 'number' - 'number' / 'member'
        elif mode == 2:
            if key and self.construction_dict[key]['token_pos'] == corr_token['token_pos'] and \
                    self.construction_dict[key]['token_tag'] == corr_token['token_tag']:
                return key, self.construction_dict[key]

            for token_id, error_token in self.construction_dict.items():
                if error_token['token_pos'] == corr_token['token_pos'] and \
                        error_token['token_tag'] == corr_token['token_tag']:
                    return token_id, error_token
        return None, {}

    def token_in_correction(self, mode, missing=True):
        for corr_id, correction in self.correction.items():
            # prepositions
            if mode == 1:
                if correction['token_tag'] in self.prepositions:
                    return corr_id, correction
            # modals
            elif mode == 2:
                if self.is_modal(correction):
                    return corr_id, correction
            # articles
            elif mode == 3:
                if correction['token'].lower() in self.articles:
                    return corr_id, correction
            # conjunctions
            elif mode == 4:
                if self.is_conjunction(correction):
                    return corr_id, correction
            # pronouns
            elif mode == 5:
                if correction['token_pos'] == 'PRON':
                    return corr_id, correction

            # degree of comparison
            elif mode == 7:
                if self.is_comparative(correction):
                    return corr_id, correction

            # comma for relative clauses
            elif mode == 8:
                if correction['token_pos'] == 'PUNCT' and correction['token'] == ',':
                    # ", which"
                    if corr_id + 1 in self.construction_dict.keys():
                        right_token = self.construction_dict[corr_id + 1]
                        if right_token['token'] in self.relative_conj:
                            return corr_id, correction
                    # " , which is important for the international trade, "
                    for token_id, token in self.sentence_tokens.items():
                        if token_id < corr_id and token['token'] in self.relative_conj:
                            return corr_id, correction

            # conjunction for relative clauses
            elif mode == 9:
                if correction['token'] in self.relative_conj:
                    return corr_id, correction

        return 0, {}

    def token_in_error(self, mode, missing=True):
        for error_id, error_token in self.construction_dict.items():
            # comma for relative clauses
            if mode == 9:
                if error_token['token_pos'] == 'PUNCT' and error_token['token'] == ',':
                    # ", which"
                    if error_id + 1 in self.construction_dict.keys():
                        right_token = self.construction_dict[error_id + 1]
                        if right_token['token'] in self.relative_conj:
                            return error_id, error_token
                    # " , which is important for the international trade, "
                    for token_id, token in self.sentence_tokens.items():
                        if token_id < error_id and token['token'] in self.relative_conj:
                            return error_id, error_token
            # conjunction for relative clauses
            elif mode == 9:
                if error_token['token'] in self.relative_conj:
                    return error_id, error_token

        return 0, {}

    def find_comparative_construction(self, correction=0):
        construction = {}

        if not correction:
            for token_id, token in self.construction_dict.items():
                # "as ... as"
                # "twice as many", "twice as much", "twice as often"
                if token['token'] == 'as' and len(token['ancestor_list']):
                    construction[token_id] = token
                    for a in token['ancestor_list']:
                        ancestor = self.sentence_tokens[a[1]]
                        if ancestor['token_pos'] in ['ADJ', 'ADV'] and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0] == 'as':
                                    if a[1] not in construction.keys():
                                        construction[a[1]] = ancestor
                                    construction[c[1]] = self.sentence_tokens[c[1]]
                                else:
                                    child = self.full_correction[c[1]]
                                    if child['token_pos'] in ['ADJ', 'ADV']:
                                        construction[c[1]] = child
                            return construction

                # "more modern than", "less money than", "use more than them"
                if token['token'] in ['more', 'less'] and len(token['ancestor_list']):
                    construction[token_id] = token
                    for a in token['ancestor_list']:
                        ancestor = self.sentence_tokens[a[1]]
                        if ancestor['token_pos'] == 'NOUN' and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0] == 'than':
                                    if a[1] not in construction.keys():
                                        construction[a[1]] = ancestor
                                    construction[c[1]] = self.sentence_tokens[c[1]]
                                    return construction

                    for a in token['ancestor_list']:
                        ancestor = self.sentence_tokens[a[1]]
                        if ancestor['token_pos'] in ['VERB', 'AUX'] and len(token['children_list']):
                            for c in token['children_list']:
                                if c[0] == 'than':
                                    if a[1] not in construction.keys():
                                        construction[a[1]] = ancestor
                                    construction[c[1]] = self.sentence_tokens[c[1]]
                                    return construction

                # "the higher you get, the harder you fall" - we try to restore the parallel comparative construction
                if self.is_comparative(token):
                    # "the more important", "the more often"
                    if token['token_pos'] == 'ADV' and len(token['ancestor_list']):
                        for a in token['ancestor_list']:
                            ancestor = self.sentence_tokens[a[1]]
                            if ancestor in ['ADJ', 'ADV']:
                                token_id = a[1]
                                token = ancestor

                    if token['token_pos'] in ['ADJ', 'ADV'] and len(token['ancestor_list']):
                        construction[token_id] = token
                        for a in token['ancestor_list']:
                            ancestor = self.sentence_tokens[a[1]]
                            if ancestor['token_pos'] in ['VERB', 'AUX'] and a[1] > self.current_token_id and \
                                    len(ancestor['ancestor_list']):
                                construction[a[1]] = ancestor
                                for aa in ancestor['ancestor_list']:
                                    ancestor_anc = self.sentence_tokens[aa[1]]
                                    if ancestor_anc['token_pos'] in ['VERB', 'AUX'] and len(token['children_list']):
                                        construction[aa[1]] = ancestor_anc
                                        for c in token['children_list']:
                                            child = self.sentence_tokens[c[1]]
                                            if child['token_pos'] == 'ADJ':
                                                if self.is_comparative(child):
                                                    construction[c[1]] = child
                                                    return construction
                                                elif len(child['children_list']):
                                                    for cc in child['children_list']:
                                                        child_child = self.sentence_tokens[cc[1]]
                                                        if child['token_pos'] == 'ADV' and \
                                                                self.is_comparative(child_child):
                                                            construction[c[1]] = child
                                                            construction[cc[1]] = child_child
                                                            return construction
        else:
            for token_id, token in self.full_correction.items():
                # "as ... as"
                # "twice as many", "twice as much", "twice as often"
                if token['token'].lower() == 'as' and len(token['ancestor_list']):
                    construction[token_id] = token
                    for a in token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] in ['ADJ', 'ADV'] and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0] == 'as':
                                    if a[1] not in construction.keys():
                                        construction[a[1]] = ancestor
                                    construction[c[1]] = self.full_correction[c[1]]
                                else:
                                    child = self.full_correction[c[1]]
                                    if child['token_pos'] in ['ADJ', 'ADV']:
                                        construction[c[1]] = child
                            return construction

                # "more modern than", "less money than", "use more than them"
                if token['token'].lower() in ['more', 'less'] and len(token['ancestor_list']):
                    construction[token_id] = token
                    for a in token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] == 'NOUN' and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0].lower() == 'than':
                                    if a[1] not in construction.keys():
                                        construction[a[1]] = ancestor
                                    construction[c[1]] = self.full_correction[c[1]]
                                    return construction

                    for a in token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] in ['VERB', 'AUX'] and len(token['children_list']):
                            for c in token['children_list']:
                                if c[0] == 'than':
                                    if a[1] not in construction.keys():
                                        construction[a[1]] = ancestor
                                    construction[c[1]] = self.full_correction[c[1]]
                                    return construction

                # "the higher you get, the harder you fall" - we try to restore the parallel comparative construction
                if self.is_comparative(token):
                    # "the more important", "the more often"
                    if token['token_pos'] == 'ADV' and len(token['ancestor_list']):
                        for a in token['ancestor_list']:
                            ancestor = self.full_correction[a[1]]
                            if ancestor in ['ADJ', 'ADV']:
                                token_id = a[1]
                                token = ancestor

                    if token['token_pos'] in ['ADJ', 'ADV'] and len(token['ancestor_list']):
                        construction[token_id] = token
                        for a in token['ancestor_list']:
                            ancestor = self.full_correction[a[1]]
                            if ancestor['token_pos'] in ['VERB', 'AUX'] and a[1] > self.current_token_id and \
                                    len(ancestor['ancestor_list']):
                                construction[a[1]] = ancestor
                                for aa in ancestor['ancestor_list']:
                                    if aa[1] in self.full_correction.keys():
                                        ancestor_anc = self.full_correction[aa[1]]
                                        if ancestor_anc['token_pos'] in ['VERB', 'AUX'] and len(
                                                token['children_list']):
                                            construction[aa[1]] = ancestor_anc
                                            for c in token['children_list']:
                                                child = self.full_correction[c[1]]
                                                if child['token_pos'] == 'ADJ':
                                                    if self.is_comparative(child):
                                                        construction[c[1]] = child
                                                        return construction
                                                    elif len(child['children_list']):
                                                        for cc in child['children_list']:
                                                            if cc[1] in self.full_correction.keys():
                                                                child_child = self.full_correction[cc[1]]
                                                                if child['token_pos'] == 'ADV' and \
                                                                        self.is_comparative(child_child):
                                                                    construction[c[1]] = child
                                                                    construction[cc[1]] = child_child
                                                                    return construction
        return {}

    """
    Rules that broaden error span and correction
    """

    def articles_span(self, error_article, corr_article):
        error = {}
        error_text, correction_text = '', ''
        idx_1, idx_2 = 0, 0

        # "a number" - "the number"
        # "a same size" - "the same size"
        # "the girls" - "girls"
        if len(error_article):
            article = error_article[1]
            error[error_article[0]] = article
            if len(article['ancestor_list']):
                for a in self.error_properties['ancestor_list']:
                    ancestor = self.construction_dict[a[1]]
                    if ancestor['token_pos'] == 'NOUN':
                        error[a[1]] = ancestor
                        if len(ancestor['children_list']) > 1:
                            for c in ancestor['children_list']:
                                if c[1] > error_article[0]:
                                    error[c[1]] = self.construction_dict[c[1]]
                        break

        # "a number" - "the number"
        # "a same size" - "the same size"
        # "good film" - "a good film"
        elif len(corr_article):
            article = corr_article[1]
            if len(article['ancestor_list']):
                for a in article['ancestor_list']:
                    ancestor = self.full_correction[a[1]]
                    if ancestor['token_pos'] == 'NOUN':
                        token_id, error_match = self.match_error_token(ancestor, a[1], 1)
                        if len(error_match.keys()):
                            error[token_id] = error_match
                            if len(error_match['children_list']) > 1:
                                for c in error_match['children_list']:
                                    error[c[1]] = self.construction_dict[c[1]]
                        break

        if len(error.keys()):
            error = dict(sorted(error.items()))
            for error_token in error.values():
                if error_text == '':
                    idx_1 = error_token['idx_1']
                error_text += ' ' + error_token['token'] if error_text != '' else error_token['token']
                idx_2 = error_token['idx_2'] if error_token['idx_2'] > idx_2 else idx_2

        without_article = ' '.join(error_text.split()[1:]) if len(error_article) else error_text
        correction_text = corr_article[1]['token'] + ' ' + without_article if len(corr_article) else without_article
        return [error_text, idx_1, idx_2], correction_text

    def comma_in_sentence(self, closing=False):
        relative_conj = 0

        for token_id, token in self.sentence_tokens.items():
            if token['token'] in self.relative_conj:
                relative_conj = 1
            if token['token_pos'] == 'PUNCT' and token['token'] == ',':
                if not closing:
                    right_token = self.sentence_tokens[token_id + 1]
                    if right_token['token'] in self.relative_conj:
                        return token_id, token
                elif closing and relative_conj:
                    return token_id, token

        return 0, {}

    def prepositions_span(self, error_prep, corr_prep, tag):
        error = {}
        error_text, correction_text = '', ''
        idx_1, idx_2 = 0, 0

        # "into" - "to" (Prepositions)
        # "reasons of" - "reasons for" (Prepositional noun)
        # "popular for" - "popular among" (Prepositional adjective)
        # "independently on" - "independently of" (Prepositional adverb)

        if len(error_prep):
            preposition = error_prep[1]
            error[error_prep[0]] = preposition
            if len(preposition['ancestor_list']):
                for a in preposition['ancestor_list']:
                    ancestor = self.construction_dict[a[1]]
                    if (tag == 18 and ancestor['token_pos'] == 'NOUN') or \
                            (tag == 25 and ancestor['token_pos'] == 'ADJ') or \
                            (tag == 28 and ancestor['token_pos'] == 'ADV'):
                        error[a[1]] = ancestor
                        break

        elif len(corr_prep):
            preposition = corr_prep[1]
            if len(preposition['ancestor_list']):
                for a in preposition['ancestor_list']:
                    ancestor = self.full_correction[a[1]]
                    if (tag == 18 and ancestor['token_pos'] == 'NOUN') or \
                            (tag == 25 and ancestor['token_pos'] == 'ADJ') or \
                            (tag == 28 and ancestor['token_pos'] == 'ADV'):
                        token_id, error_match = self.match_error_token(ancestor, a[1], 1)
                        if len(error_match.keys()) and len(error_match['children_list']):
                            error[token_id] = error_match
                        break

        if len(error.keys()):
            error = dict(sorted(error.items()))
            for error_token in error.values():
                if error_text == '':
                    idx_1 = error_token['idx_1']
                error_text += ' ' + error_token['token'] if error_text != '' else error_token['token']
                idx_2 = error_token['idx_2'] if error_token['idx_2'] > idx_2 else idx_2

        without_preposition = error_text.split()[0] if len(error_prep) else error_text
        correction_text = without_preposition + ' ' + corr_prep[1]['token'] if len(corr_prep) else without_preposition
        return [error_text, idx_1, idx_2], correction_text

    def possessive_span(self, error_token, apostrophe=0):
        error, correction = {}, {}
        error_text, correction_text = '', ''
        idx_1, idx_2 = 0, 0

        if apostrophe:
            # "'" (apostrophe) in the error span, "s" in the correction
            # we have to change that to error token + apostrophe in the error span and error token + s in the correction
            error = self.sentence_tokens[self.current_token_id - 1]
            error_text = error['token'] + error_token['token']
            idx_1, idx_2 = error['idx_1'], error_token['idx_2']
            correction_text = error['token']
            for correction in self.correction.values():
                correction_text += correction['token']
        else:
            # "shoes pair" - "pair of shoes"
            error[self.current_token_id] = error_token
            if len(error_token['ancestor_list']):
                for a in error_token['ancestor_list']:
                    if a[1] in self.construction_dict.keys():
                        ancestor = self.construction_dict[a[1]]
                        if ancestor['token_pos'] == 'NOUN':
                            error[a[1]] = ancestor
                            break

            corr_id, corr_token = self.match_correction(error_token, mode=1)
            correction[corr_id] = corr_token
            if len(corr_token['children_list']):
                for c in corr_token['children_list']:
                    if c[1] > corr_id:
                        child = self.full_correction[c[1]]
                        if child['token_tag'] in self.prepositions and child['token_pos'] == 'ADP':
                            correction[c[1]] = child
                            if len(child['children_list']):
                                for cc in child['children_list']:
                                    if cc[1] > c[1]:
                                        child_child = self.full_correction[cc[1]]
                                        if child_child['token_pos'] == 'NOUN':
                                            correction[cc[1]] = child_child
                                            break
                            break
            if not len(correction.keys()):
                correction = self.correction

            error = dict(sorted(error.items()))
            for error_token in error.values():
                if error_text == '':
                    idx_1 = error_token['idx_1']
                error_text += ' ' + error_token['token'] if error_text != '' else error_token['token']
                idx_2 = error_token['idx_2'] if error_token['idx_2'] > idx_2 else idx_2

            correction = dict(sorted(correction.items()))
            for corr_token in correction.values():
                correction_text += ' ' + corr_token['token'] if correction_text != '' else corr_token['token']

        return [error_text, idx_1, idx_2], correction_text

    def comparative_construction_span(self, error_token, tag):
        degrees = ['more', 'less', 'most', 'least']
        error, correction = {}, {}
        error_text, correction_text = '', ''
        idx_1, idx_2 = 0, 0

        # degree of comparison
        if tag == 29:
            if self.is_comparative(error_token):
                error[self.current_token_id] = error_token
                if error_token['token'] in degrees and len(error_token['ancestor_list']):
                    for a in error_token['ancestor_list']:
                        if a[1] <= self.current_token_id + 2 and a[1] in self.construction_dict.keys():
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token_pos'] in ['ADJ', 'ADV']:
                                error[a[1]] = ancestor
                                if error_token['token'] in ['most', 'least'] and \
                                        self.sentence_tokens[self.current_token_id - 1]['token'] == 'the':
                                    error[self.current_token_id - 1] = self.sentence_tokens[self.current_token_id - 1]
                                break
                        elif a[1] > self.current_token_id + 2:
                            break
            elif error_token['token_pos'] in ['ADJ', 'ADV'] and len(error_token['children_list']):
                for c in error_token['children_list']:
                    if c[1] in self.construction_dict.keys():
                        child = self.construction_dict[c[1]]
                        if self.is_comparative(child):
                            error[c[1]] = child
                            if child['token'] in ['most', 'least'] and \
                                    self.sentence_tokens[c[1] - 1]['token'] == 'the':
                                error[c[1] - 1] = self.sentence_tokens[c[1] - 1]
                            break

            corr_id, corr_token = self.token_in_correction(mode=7, missing=False)
            if self.is_comparative(corr_token):
                correction[corr_id] = corr_token
                if corr_token['token'] in degrees and len(corr_token['ancestor_list']):
                    for a in corr_token['ancestor_list']:
                        if a[1] <= corr_id + 2:
                            ancestor = self.full_correction[a[1]]
                            if ancestor['token_pos'] in ['ADJ', 'ADV']:
                                correction[a[1]] = ancestor
                                if corr_token['token'] in ['most', 'least'] and \
                                        self.full_correction[corr_id - 1]['token'] == 'the':
                                    correction[corr_id - 1] = self.full_correction[corr_id - 1]
                                break
                        elif a[1] > corr_id + 2:
                            break
            elif corr_token['token_pos'] in ['ADJ', 'ADV'] and len(corr_token['children_list']):
                for c in corr_token['children_list']:
                    if c[1] in self.full_correction.keys():
                        child = self.full_correction[c[1]]
                        if self.is_comparative(child):
                            correction[c[1]] = child
                            if child['token'] in ['most', 'least'] and \
                                    self.full_correction[c[1] - 1]['token'] == 'the':
                                correction[c[1] - 1] = self.full_correction[c[1] - 1]
                            break

        # comparative construction
        elif tag == 37:
            error = self.find_comparative_construction(correction=0)
            correction = self.find_comparative_construction(correction=1)

        if not len(error.keys()):
            error[self.current_token_id] = self.error_properties
        if not len(correction.keys()):
            correction = self.correction

        error = dict(sorted(error.items()))
        for error_token in error.values():
            if error_text == '':
                idx_1 = error_token['idx_1']
            error_text += ' ' + error_token['token'] if error_text != '' else error_token['token']
            idx_2 = error_token['idx_2'] if error_token['idx_2'] > idx_2 else idx_2

        correction = dict(sorted(correction.items()))
        for corr_token in correction.values():
            correction_text += ' ' + corr_token['token'] if correction_text != '' else corr_token['token']

        return [error_text, idx_1, idx_2], correction_text

    def verb_span(self, error_token):
        error, correction = {}, {}
        error_text, correction_text = '', ''
        idx_1, idx_2 = 0, 0

        if error_token['token_pos'] == 'AUX' and len(error_token['ancestor_list']):
            for a in error_token['ancestor_list']:
                if a[1] >= self.current_token_id - 1 and a[1] <= self.current_token_id + 2:
                    ancestor = self.construction_dict[a[1]]
                    if ancestor['token_pos'] == 'VERB':
                        error_token = ancestor
                        break
                elif a[1] < self.current_token_id - 1 or a[1] > self.current_token_id + 2:
                    break

        error[self.current_token_id] = error_token
        if len(error_token['children_list']):
            for c in error_token['children_list']:
                if c[1] in self.construction_dict.keys() and c[1] <= self.current_token_id + 2:
                    child = self.construction_dict[c[1]]
                    if child['token_pos'] == 'PUNCT' and c[1] < self.current_token_id:
                        new_error = {}
                        new_error[self.current_token_id] = error_token
                        error = new_error
                    elif child['token_pos'] == 'AUX' and c[1] < self.current_token_id:
                        error[c[1]] = child
                        if c[1] < self.current_token_id - 1:
                            for token_id, token in self.construction_dict.items():
                                if token_id > c[1] and token_id < self.current_token_id:
                                    error[token_id] = token
                                elif token_id > self.current_token_id:
                                    break
                        break
                    # elif child['token_tag'] in self.prepositions and child['token'] not in ['if', 'because']:
                    elif child['token_tag'] in self.prepositions and child['token_pos'] == 'ADP':
                        error[c[1]] = child
                elif c[1] > self.current_token_id + 2:
                    break

        corr_id, corr_token = self.match_correction(error_token, 3)
        correction[corr_id] = corr_token
        if len(corr_token['children_list']):
            for cc in corr_token['children_list']:
                child = self.full_correction[cc[1]]
                if child['token_pos'] == 'PUNCT' and cc[1] < corr_id:
                    new_correction = {}
                    new_correction[corr_id] = corr_token
                    correction = new_correction
                elif child['token_pos'] == 'AUX' and cc[1] < corr_id:
                    correction[cc[1]] = child
                    if cc[1] < corr_id - 1:
                        for token_id, token in self.full_correction.items():
                            if token_id > cc[1] and token_id < corr_id:
                                correction[token_id] = token
                            elif token_id > corr_id:
                                break
                    break
                elif child['token_tag'] in self.prepositions and child['token_pos'] == 'ADP':
                    correction[cc[1]] = child
                elif cc[1] > corr_id + 2:
                    break
        if len(corr_token['ancestor_list']):
            for aa in corr_token['ancestor_list']:
                if aa[1] >= corr_id - 2:
                    ancestor = self.full_correction[aa[1]]
                    if ancestor['token_pos'] == 'AUX' or ancestor['token'] == 'to':
                        correction[aa[1]] = ancestor
                else:
                    break

        if not len(correction.keys()):
            correction = self.correction

        error = dict(sorted(error.items()))
        for error_token in error.values():
            if error_text == '':
                idx_1 = error_token['idx_1']
            error_text += ' ' + error_token['token'] if error_text != '' else error_token['token']
            idx_2 = error_token['idx_2'] if error_token['idx_2'] > idx_2 else idx_2

        correction = dict(sorted(correction.items()))
        for corr_token in correction.values():
            correction_text += ' ' + corr_token['token'] if correction_text != '' else corr_token['token']

        return [error_text, idx_1, idx_2], correction_text

    def modals_span(self, error_token, modal_error=1):
        error, correction = {}, {}
        error_text, correction_text = '', ''
        idx_1, idx_2 = 0, 0
        additional_tokens = 0

        error[self.current_token_id] = error_token

        if (modal_error):
            # "has to become" - "must become"
            if error_token['token_pos'] == 'VERB' and error_token['token_lemma'] == 'have':
                if self.current_token_id + 1 in self.construction_dict.keys():
                    prep_to = self.construction_dict[self.current_token_id + 1]
                    if prep_to['token_lemma'] == 'to':
                        error[self.current_token_id + 1] = prep_to

            if self.token_in_correction(mode=2, missing=False):
                corr_id, corr_token = self.match_correction(error_token, 4)
                correction[corr_id] = corr_token
                if corr_token['token_lemma'] in ['have', 'ought'] and corr_id + 1 in self.full_correction.keys():
                    prep_to = self.full_correction[corr_id + 1]
                    if prep_to['token'] == 'to':
                        correction[corr_id + 1] = prep_to
            else:
                # "can differ" - "differs"
                correction = self.correction
                if len(error_token['ancestor_list']):
                    for a in error_token['ancestor_list']:
                        if a[1] in self.construction_dict.keys():
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token_pos'] == 'VERB':
                                error[a[1]] = ancestor
                                break
        else:
            corr_id, corr_token = self.token_in_correction(mode=2, missing=False)
            correction[corr_id] = corr_token
            if len(corr_token['ancestor_list']):
                for a in corr_token['ancestor_list']:
                    ancestor = self.full_correction[a[1]]
                    if ancestor['token_pos'] == 'VERB':
                        correction[a[1]] = ancestor
                        if a[1] > corr_id + 1:
                            for token_id, token in self.full_correction.items():
                                if token_id > corr_id and token_id < a[1]:
                                    correction[token_id] = token
                                    additional_tokens = 1
                                elif token_id > a[1]:
                                    break
                        break

            if additional_tokens and len(error_token['children_list']):
                for c in error_token['children_list']:
                    if c[1] in self.construction_dict.keys():
                        error[c[1]] = self.construction_dict[c[1]]

        error = dict(sorted(error.items()))
        for error_token in error.values():
            if error_text == '':
                idx_1 = error_token['idx_1']
            error_text += ' ' + error_token['token'] if error_text != '' else error_token['token']
            idx_2 = error_token['idx_2'] if error_token['idx_2'] > idx_2 else idx_2

        correction = dict(sorted(correction.items()))
        for corr_token in correction.values():
            correction_text += ' ' + corr_token['token'] if correction_text != '' else corr_token['token']

        return [error_text, idx_1, idx_2], correction_text

    def gerund_part_inf_span(self, error_token):
        error, correction = {}, {}
        error_text, correction_text = '', ''
        idx_1, idx_2 = 0, 0
        aux_in_error, aux_in_corr = 0, 0
        prep_in_error, prep_in_corr = 0, 0

        if error_token['token_pos'] == 'VERB' and len(error_token['children_list']):
            error[self.current_token_id] = error_token
            for c in error_token['children_list']:
                if c[1] in self.construction_dict.keys() and c[1] < self.current_token_id + 3:
                    child = self.construction_dict[c[1]]
                    if child['token_pos'] == 'PUNCT' and c[1] < self.current_token_id:
                        new_error = {}
                        new_error[self.current_token_id] = error_token
                        error = new_error
                    elif child['token_pos'] == 'AUX' and c[1] < self.current_token_id and not aux_in_error:
                        error[c[1]] = child
                        aux_in_error = 1
                        if c[1] < self.current_token_id - 1:
                            for token_id, token in self.construction_dict.items():
                                if token_id > c[1] and token_id < self.current_token_id:
                                    error[token_id] = token
                                elif token_id > self.current_token_id:
                                    break
                    elif child['token_pos'] in ['PRF', 'PRP', 'ADP', 'IN'] or child['token'] == 'to':
                        if c[1] < self.current_token_id and not prep_in_error:
                            error[c[1]] = child
                            prep_in_error = 1
                        elif c[1] > self.current_token_id:
                            if c[1] >= self.current_token_id + 1:
                                if self.current_token_id + 1 in error.keys():
                                    error[c[1]] = child
                            else:
                                error[c[1]] = child
                else:
                    break

            # "of dedicating" - "to dedicate"
            # "feel encourage" - "feel encouraged"
            if len(error_token['ancestor_list']):
                for a in error_token['ancestor_list']:
                    if a[1] in self.construction_dict.keys() and \
                            a[1] < self.current_token_id and a[1] >= self.current_token_id - 3:
                        ancestor = self.construction_dict[a[1]]
                        if ancestor['token_tag'] in self.prepositions or \
                                (not aux_in_error and ancestor['token_pos'] in ['AUX', 'VERB']):
                            error[a[1]] = ancestor
                            for token_id, token in self.construction_dict.items():
                                if token_id > a[1] and token_id < self.current_token_id:
                                    error[token_id] = token
                                elif token_id > self.current_token_id:
                                    break
                    elif a[1] > self.current_token_id:
                        break

            corr_id, corr_token = self.match_correction(error_token, 3)
            correction[corr_id] = corr_token
            if len(corr_token['children_list']):
                for cc in corr_token['children_list']:
                    if cc[1] < corr_id + 3:
                        child = self.full_correction[cc[1]]
                        if child['token_pos'] == 'PUNCT' and cc[1] < corr_id:
                            new_corr = {}
                            new_corr[corr_id] = corr_token
                            correction = new_corr
                        elif child['token_pos'] == 'AUX' and cc[1] < corr_id and not aux_in_corr:
                            correction[cc[1]] = child
                            aux_in_corr = 1
                            if cc[1] < corr_id - 1:
                                for token_id, token in self.full_correction.items():
                                    if token_id > cc[1] and token_id < corr_id:
                                        correction[token_id] = token
                                    elif token_id > corr_id:
                                        break
                        elif child['token_pos'] in ['PRF', 'PRP', 'ADP', 'IN'] or child['token'] == 'to':
                            if cc[1] < corr_id and not prep_in_corr:
                                correction[cc[1]] = child
                                prep_in_corr = 1
                            elif cc[1] >= corr_id + 1:
                                if corr_id + 1 in correction.keys():
                                    correction[cc[1]] = child
                            else:
                                correction[cc[1]] = child
                    else:
                        break

            # "of dedicating" - "to dedicate"
            # "feel encourage" - "feel encouraged"
            if len(corr_token['ancestor_list']):
                for aa in corr_token['ancestor_list']:
                    if aa[1] < corr_id and aa[1] >= corr_id - 3:
                        ancestor = self.full_correction[aa[1]]
                        if ancestor['token_tag'] in self.prepositions or \
                                (not aux_in_corr and ancestor['token_pos'] in ['VERB', 'AUX']):
                            correction[aa[1]] = ancestor
                            for token_id, token in self.full_correction.items():
                                if token_id > aa[1] and token_id < corr_id:
                                    correction[token_id] = token
                                elif token_id > corr_id:
                                    break
                    elif aa[1] > corr_id:
                        break

        if not len(error.keys()):
            error = error_token
        if not len(correction.keys()):
            correction = self.correction

        error = dict(sorted(error.items()))
        for error_token in error.values():
            if error_text == '':
                idx_1 = error_token['idx_1']
            error_text += ' ' + error_token['token'] if error_text != '' else error_token['token']
            idx_2 = error_token['idx_2'] if error_token['idx_2'] > idx_2 else idx_2

        correction = dict(sorted(correction.items()))
        for corr_token in correction.values():
            correction_text += ' ' + corr_token['token'] if correction_text != '' else corr_token['token']

        return [error_text, idx_1, idx_2], correction_text
