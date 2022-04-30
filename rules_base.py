from dictionaries import irregular_verbs, pos_dict
import re


class RulesBase:
    articles = ['a', 'an', 'the']
    # as many of quantifiers are annotated as regular adjectives,
    # the simplest way of identifying them is by making a list of them
    quantifiers = ['much', 'many', 'less', 'few', 'fewer', 'lot']
    relative_conj = ['who', 'that', 'which', 'whose', 'where', 'why']
    coordinating_conj = ['and', 'or', 'nor', 'but', 'either', 'neither']

    # quantifiers = ['JJ', 'JJR', 'RBS']
    modals = ['MD', 'VM0']
    prepositions = ['PRF', 'PRP', 'ADP', 'IN']
    conjunctions = ['CCONJ', 'SCONJ']

    subjects = ['csubj', 'csubjpass', 'nsubj', 'nsubjpass']
    gerund = ['VBG', 'VDG', 'VHG', 'VVG']
    participle = ['VBN', 'VDN', 'VHN', 'VVN']
    aux = ['is', 'are', 'was', 'were', 'has', 'have', 'had']

    gerund_verbs = ['acknowledge', 'admit', 'allow', 'anticipate', 'appreciate', 'avoid', 'begin',
                    'bear', 'confess', 'consider', 'continue', 'defend', 'delay', 'detest', 'discuss',
                    'dislike', 'enjoy', 'escape', 'evade', 'explain', 'fear', 'finish', 'forget', 'forgive',
                    'hate', 'keep', 'like', 'love', 'miss', 'permit', 'practice', 'prefer', 'prevent',
                    'propose', 'quit', 'recall', 'recollect', 'recommend', 'regret', 'remember', 'report',
                    'resent', 'resist', 'resume', 'risk', 'stand', 'start', 'stop', 'suggest', 'support',
                    'try', 'understand']

    infinitive_verbs = ['afford', 'agree', 'appear', 'arrange', 'ask', 'attempt', 'beg', 'begin', 'bear',
                        'care', 'chance', 'choose', 'claim', 'come', 'consent', 'continue', 'dare', 'decide',
                        'demand', 'deserve', 'determine', 'elect', 'expect', 'fail', 'forget', 'get', 'guarantee',
                        'hate', 'hesitate', 'hope', 'hurry', 'learn', 'like', 'love', 'manage', 'mean',
                        'need', 'neglect', 'offer', 'pay', 'plan', 'prefer', 'prepare', 'pretend', 'promise',
                        'propose', 'prove', 'quit', 'refuse', 'regret', 'remain', 'remember', 'request', 'resolve',
                        'say', 'seek', 'seem', 'stand', 'start', 'stop', 'struggle', 'swear', 'tend', 'threaten',
                        'try', 'wait', 'want', 'wish']

    def __init__(self):
        self.construction_dict = {}
        self.correction = {}
        self.error_properties = {}
        self.full_correction = {}
        self.full_error = {}
        self.current_token_id = None
        self.error_span = []
        self.correction_span = ''
        self.sentence_tokens = {}

    """
    Check whether token exists in the error span or correction
    """

    def match_correction(self, error_properties, mode):
        # POS-tag: 'number' - 'number' / 'member' / 'amounts'
        if mode == 1:
            for corr_id, correction in self.correction.items():
                if correction['token_pos'] == error_properties['token_pos']:
                    return corr_id, correction

        # POS-tag + token_head
        elif mode == 2:
            for corr_id, correction in self.correction.items():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_head'] == error_properties['token_head']:
                    return corr_id, correction

        # 'get' - 'getting'; 'encourage' - 'encouraged'; POS-tag: VERB or AUX
        elif mode == 3:
            if self.is_gerund(error_properties):
                for corr_id, correction in self.correction.items():
                    if correction['token_pos'] == 'NOUN':
                        return corr_id, correction
            for corr_id, correction in self.correction.items():
                if correction['token_pos'] == 'VERB' or correction['token_pos'] == 'AUX' or \
                        (correction['token_pos'] == 'NOUN' and correction['token'].endswith('ing')) or \
                        (correction['token_pos'] == 'ADJ' and correction['token'].endswith('ed')):
                    return corr_id, correction

        # modals
        elif mode == 4:
            for corr_id, correction in self.correction.items():
                if self.is_modal(correction):
                    return corr_id, correction

        # conjunctions
        elif mode == 5:
            for corr_id, correction in self.correction.items():
                if self.is_conjunction(correction):
                    return corr_id, correction

        # numerals
        elif mode == 6:
            for corr_id, correction in self.correction.items():
                if self.is_numeral(correction):
                    return corr_id, correction

        # degree of comparison
        elif mode == 7:
            for corr_id, correction in self.correction.items():
                if self.is_comparative(correction):
                    return corr_id, correction

        # determiners
        elif mode == 9:
            for corr_id, correction in self.correction.items():
                if correction['token_tag'] == 'DT' and not correction['token'].lower() in self.articles:
                    return corr_id, correction

        # quantifiers
        elif mode == 10:
            for corr_id, correction in self.correction.items():
                if correction['token'].lower() in self.quantifiers:
                    return corr_id, correction

        # negation
        elif mode == 13:
            for corr_id, correction in self.correction.items():
                if self.is_negative(correction):
                    return corr_id, correction

        # POS-tag + lemma: 'number' - 'number'
        else:
            for corr_id, correction in self.correction.items():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_tag'] == error_properties['token_tag'] and \
                        correction['token_lemma'] == error_properties['token_lemma']:
                    return corr_id, correction
        return None, {}

    def token_in_correction(self, mode, missing=True):
        for corr_id, correction in self.correction.items():
            # prepositions
            if mode == 1:
                if correction['token_tag'] in self.prepositions:
                    return False if missing else True

            # modals
            elif mode == 2:
                if self.is_modal(correction):
                    return False if missing else True

            # articles
            elif mode == 3:
                if correction['token'].lower() in self.articles:
                    return False if missing else True

            # conjunctions
            elif mode == 4:
                if self.is_conjunction(correction):
                    return False if missing else True

            # pronouns
            elif mode == 5:
                if correction['token_pos'] == 'PRON' and correction['token_tag'] != 'DT':
                    return False if missing else True

            # numerals
            elif mode == 6:
                if self.is_numeral(correction):
                    return False if missing else True

            # degree of comparison
            elif mode == 7:
                if self.is_comparative(correction):
                    return False if missing else True

            # comma for relative clauses
            elif mode == 8:
                if correction['token_pos'] == 'PUNCT' and correction['token'] == ',':
                    # ", which"
                    if corr_id + 1 in self.full_correction.keys():
                        right_token = self.full_correction[corr_id + 1]
                        if right_token['token'].lower() in self.relative_conj:
                            return False if missing else True
                    # " , which is important for the international trade, "
                    for token_id, token in self.sentence_tokens.items():
                        if token_id < corr_id and token['token'].lower() in self.relative_conj:
                            return False if missing else True

            # determiners
            elif mode == 9:
                if correction['token_tag'] == 'DT' and not correction['token'].lower() in self.articles:
                    return False if missing else True

            # quantifiers
            elif mode == 10:
                if correction['token'].lower() in self.quantifiers:
                    return False if missing else True

            # token from comparative construction
            elif mode == 11:
                if self.token_from_comparative_constr(correction):
                    return False if missing else True

            # token with apostrophe (possessive form of a noun)
            elif mode == 12:
                if "'" in correction['token']:
                    return False if missing else True

            # negation
            elif mode == 13:
                if self.is_negative(correction):
                    return False if missing else True

        return True if missing else False

    def token_in_error(self, mode, missing=True):
        if len(self.full_error['tokens'].values()):
            for error_id, error_token in self.full_error['tokens'].items():
                # prepositions
                if mode == 1:
                    if error_token['token_tag'] in self.prepositions:
                        return False if missing else True

                # comma for relative clauses
                elif mode == 8:
                    if error_token['token_pos'] == 'PUNCT' and error_token['token'] == ',':
                        # ", which"
                        if error_id + 1 in self.construction_dict.keys():
                            right_token = self.construction_dict[error_id + 1]
                            if right_token['token'].lower() in self.relative_conj:
                                return False if missing else True
                        # " , which is important for the international trade, "
                        for token_id, token in self.sentence_tokens.items():
                            if token_id < error_id and token['token'].lower() in self.relative_conj:
                                return False if missing else True

        return True if missing else False

    def find_comparative_construction(self, correction=False):
        num_as = 0
        if not correction:
            for token in self.construction_dict.values():
                # "as ... as"
                # "twice as many", "twice as much", "twice as often"
                if token['token'] == 'as' and len(token['ancestor_list']):
                    for a in token['ancestor_list']:
                        ancestor = self.sentence_tokens[a[1]]
                        if ancestor['token_pos'] in ['ADJ', 'ADV'] and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0] == 'as':
                                    num_as += 1
                            return [num_as > 0, num_as]

                # "more modern than", "less money than", "use more than them"
                if token['token'] in ['more', 'less'] and len(token['ancestor_list']):
                    for a in token['ancestor_list']:
                        ancestor = self.sentence_tokens[a[1]]
                        if ancestor['token_pos'] == 'NOUN' and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0] == 'than':
                                    num_to_return = 1 if token['token'] == 'more' else 2
                                    return [True, num_to_return]
                    for a in token['ancestor_list']:
                        ancestor = self.sentence_tokens[a[1]]
                        if ancestor['token_pos'] in ['VERB', 'AUX'] and len(token['children_list']):
                            for c in token['children_list']:
                                if c[0] == 'than':
                                    num_to_return = 1 if token['token'] == 'more' else 2
                                    return [True, num_to_return]

                # "the higher you get, the harder you fall" - we try to restore the parallel comparative construction
                if self.is_comparative(token):
                    # "the more important", "the more often"
                    if token['token_pos'] == 'ADV' and len(token['ancestor_list']):
                        for a in token['ancestor_list']:
                            ancestor = self.sentence_tokens[a[1]]
                            if ancestor in ['ADJ', 'ADV']:
                                token = ancestor

                    if token['token_pos'] in ['ADJ', 'ADV'] and len(token['ancestor_list']):
                        for a in token['ancestor_list']:
                            ancestor = self.sentence_tokens[a[1]]
                            if ancestor['token_pos'] in ['VERB', 'AUX'] and a[1] > self.current_token_id and \
                                    len(ancestor['ancestor_list']):
                                for aa in ancestor['ancestor_list']:
                                    ancestor_anc = self.sentence_tokens[aa[1]]
                                    if ancestor_anc['token_pos'] in ['VERB', 'AUX'] and len(token['children_list']):
                                        for c in token['children_list']:
                                            child = self.sentence_tokens[c[1]]
                                            if child['token_pos'] == 'ADJ':
                                                if self.is_comparative(child):
                                                    return True
                                                elif len(child['children_list']):
                                                    for cc in child['children_list']:
                                                        child_child = self.sentence_tokens[cc[1]]
                                                        if child['token_pos'] == 'ADV' and \
                                                                self.is_comparative(child_child):
                                                            return [True]
        else:
            for token_id, token in self.full_correction.items():
                # "as ... as"
                # "twice as many", "twice as much", "twice as often"
                if token['token'].lower() == 'as' and len(token['ancestor_list']):
                    for a in token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] in ['ADJ', 'ADV'] and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0] == 'as':
                                    num_as += 1
                            return [num_as > 0, num_as]

                # "more modern than", "less money than", "use more than them"
                if token['token'].lower() in ['more', 'less'] and len(token['ancestor_list']):
                    for a in token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] == 'NOUN' and len(ancestor['children_list']):
                            for c in ancestor['children_list']:
                                if c[0].lower() == 'than':
                                    num_to_return = 1 if token['token'] == 'more' else 2
                                    return [True, num_to_return]
                    for a in token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] in ['VERB', 'AUX'] and len(token['children_list']):
                            for c in token['children_list']:
                                if c[0] == 'than':
                                    num_to_return = 1 if token['token'] == 'more' else 2
                                    return [True, num_to_return]

                # "the higher you get, the harder you fall" - we try to restore the parallel comparative construction
                if self.is_comparative(token):
                    # "the more important", "the more often"
                    if token['token_pos'] == 'ADV' and len(token['ancestor_list']):
                        for a in token['ancestor_list']:
                            ancestor = self.full_correction[a[1]]
                            if ancestor in ['ADJ', 'ADV']:
                                token = ancestor

                    if token['token_pos'] in ['ADJ', 'ADV'] and len(token['ancestor_list']):
                        for a in token['ancestor_list']:
                            ancestor = self.full_correction[a[1]]
                            if ancestor['token_pos'] in ['VERB', 'AUX'] and a[1] > self.current_token_id and \
                                    len(ancestor['ancestor_list']):
                                for aa in ancestor['ancestor_list']:
                                    if aa[1] in self.full_correction.keys():
                                        ancestor_anc = self.full_correction[aa[1]]
                                        if ancestor_anc['token_pos'] in ['VERB', 'AUX'] and len(
                                                token['children_list']):
                                            for c in token['children_list']:
                                                child = self.full_correction[c[1]]
                                                if child['token_pos'] == 'ADJ':
                                                    if self.is_comparative(child):
                                                        return True
                                                    elif len(child['children_list']):
                                                        for cc in child['children_list']:
                                                            if cc[1] in self.full_correction.keys():
                                                                child_child = self.full_correction[cc[1]]
                                                                if child['token_pos'] == 'ADV' and \
                                                                        self.is_comparative(child_child):
                                                                    return [True]
        return [False]

    def allow_check_agreement(self):
        aux_found = 0

        # verbs in Past Simple, Past Perfect and Future Simple do not have number indicators
        # so if we find such a verb in the error or correction span, we do not need to check Agreement
        for error_token in self.construction_dict.values():
            if error_token['token'] in ['will', 'had']:
                return False
            elif error_token['token_pos'] == 'VERB':
                tense = error_token['token_morph'].get('Tense')
                if tense and tense[0] == 'Past':
                    if not len(error_token['children_list']):
                        return False
                    for c in error_token['children_list']:
                        if c[1] in self.construction_dict.keys():
                            child = self.construction_dict[c[1]]
                            if child['token_pos'] == 'AUX':
                                if child['token'] in ['will', 'had']:
                                    return False
                                else:
                                    aux_found = 1
                                    break
                        if not aux_found:
                            return False

        for corr_token in self.full_correction.values():
            if corr_token['token'] in ['will', 'had']:
                return False
            elif corr_token['token_pos'] == 'VERB':
                tense = corr_token['token_morph'].get('Tense')
                if tense and tense[0] == 'Past':
                    if not len(corr_token['children_list']):
                        return False
                    for c in corr_token['children_list']:
                        child = self.full_correction[c[1]]
                        if child['token_pos'] == 'AUX':
                            if child['token'] in ['will', 'had']:
                                return False
                            else:
                                aux_found = 1
                                break
                    if not aux_found:
                        return False
        return True

    """
    Basic rules
    """

    def is_numeral(self, token):
        return token['token_tag'] in pos_dict['NUM'] or \
               len(re.findall(r'\d+', token['token']))

    def is_comparative(self, token):
        degree = token['token_morph'].get('Degree')
        return degree and degree[0] in ['Cmp', 'Sup']

    def token_from_comparative_constr(self, token):
        return (token['token_pos'] == 'DET' and token['token'] not in self.articles) or \
               token['token'].lower() in ['such', 'as', 'than']

    def is_negative(self, token):
        polarity = token['token_morph'].get('Polarity')
        if polarity:
            return polarity[0] == 'Neg'
        return token['token'] in ['no', 'nothing']

    def is_modal(self, token):
        return (token['token_pos'] == 'AUX' and token['token_tag'] in self.modals) or \
               (token['token_lemma'] in ['have', 'ought'] and
                self.current_token_id + 1 in self.construction_dict.keys() and
                self.construction_dict[self.current_token_id + 1]['token'] == 'to')

    def is_finite_verb(self, token):
        verb_form = token['token_morph'].get('VerbForm')
        return verb_form and verb_form[0] in ['Fin', 'Inf']

    def is_infinitive(self, token):
        if self.is_finite_verb(token) and len(token['children_list']):
            for child in token['children_list']:
                if child[0].lower() == 'to':
                    return True
        return False

    def is_participle(self, token):
        verb_form = token['token_morph'].get('VerbForm')
        if verb_form:
            return verb_form[0] == 'Part'
        return token['token_pos'] == 'ADJ' and token['token'].endswith('ed')

    def is_gerund(self, token):
        if self.is_participle(token):
            tense = token['token_morph'].get('Tense')
            aspect = token['token_morph'].get('Aspect')
            if tense and tense[0] == 'Pres' and aspect and aspect[0] == 'Prog':
                return True
        if token['token_pos'] == 'NOUN':
            number = token['token_morph'].get('Number')
            if number and number[0] == 'Sing' and token['token'].endswith('ing'):
                return True
        return False

    def is_perfect(self, token):
        if self.is_participle(token):
            tense = token['token_morph'].get('Tense')
            aspect = token['token_morph'].get('Aspect')
            if tense and tense[0] == 'Past' and aspect and aspect[0] == 'Perf':
                return True
        if token['token_pos'] == 'ADJ' and token['token'].endswith('ed'):
            return True
        return False

    def is_conjunction(self, token):
        return (token['token_pos'] in self.conjunctions or
                (token['token_pos'] == 'PRON' and token['token_tag'] in ['WDT', 'WP']))

    """
    Word form rules
    """

    def check_irregular_form(self, form):
        irregular = irregular_verbs[self.error_properties['token_lemma']][form]
        return self.error_properties['token'] != irregular and self.full_correction['token'].lower() == irregular

    def passive_construction(self, correction=False):
        if not correction and len(self.full_error['tokens'].values()):
            # "is built", "was built", "will be built"
            for token in self.full_error['tokens'].values():
                if token['token_pos'] == 'VERB':
                    aspect = token['token_morph'].get('Aspect')
                    # "(is) argued" can be annotated either as a participle or a finite verb in the past
                    if ((aspect and aspect[0] == 'Perf' and self.is_participle(token)) or
                        token['token'].endswith('ed')) and \
                            len(token['children_list']):
                        for c in token['children_list']:
                            child = self.construction_dict[c[1]]
                            if child['token_pos'] == 'AUX':
                                return True

                elif token['token_pos'] == 'ADJ' and token['token'].endswith('ed') and \
                        len(token['ancestor_list']):
                    for a in token['ancestor_list']:
                        ancestor = self.construction_dict[a[1]]
                        if ancestor['token_pos'] == 'AUX':
                            return True

        else:
            # full passive construction in the correction span
            # "is built", "was built", "will be built"
            for correction in self.correction.values():
                if correction['token_pos'] == 'VERB':
                    aspect = correction['token_morph'].get('Aspect')
                    # "(is) argued" can be annotated either as a participle or a finite verb in the past
                    if (aspect and aspect[0] == 'Perf' and self.is_participle(correction)) or \
                            correction['token'].endswith('ed'):
                        if len(correction['children_list']):
                            for c in correction['children_list']:
                                child = self.full_correction[c[1]]
                                if child['token_pos'] == 'AUX':
                                    return True
                        if len(correction['ancestor_list']):
                            for a in correction['ancestor_list']:
                                ancestor = self.full_correction[a[1]]
                                if ancestor['token_pos'] == 'AUX':
                                    return True

                        # if there is no full passive construction in the correction area,
                        # we try to reconstruct it from the sentence, examining dependencies of error token
                        #
                        # "(is) applying" (error) - "(is) applied" (correction)
                        error_token = self.error_properties
                        if len(error_token['children_list']):
                            for c in error_token['children_list']:
                                child = self.construction_dict[c[1]]
                                if child['token_pos'] == 'AUX':
                                    return True

                elif correction['token_pos'] == 'ADJ' and correction['token'].endswith('ed'):
                    if len(correction['ancestor_list']):
                        for a in correction['ancestor_list']:
                            ancestor = self.full_correction[a[1]]
                            if ancestor['token_pos'] == 'AUX':
                                return True
                    if len(correction['children_list']):
                        for c in correction['children_list']:
                            child = self.full_correction[c[1]]
                            if child['token_pos'] == 'AUX':
                                return True

                    # if there is no full passive construction in the correction area,
                    # we try to reconstruct it from the sentence, examining dependencies of error token
                    #
                    # "(is) applying" (error) - "(is) applied" (correction)
                    error_token = self.error_properties
                    if len(error_token['ancestor_list']):
                        for a in error_token['ancestor_list']:
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token_pos'] == 'AUX':
                                return True
        return False

    def check_voice(self, correction_token):
        # "built" - "is built" / "was built"
        # "will be discussed" - "will discuss"

        passive_error = self.passive_construction(correction=False)
        passive_correction = self.passive_construction(correction=True)

        if ((passive_error and self.is_finite_verb(correction_token)) or
                not passive_error and passive_correction):
            return True

    def check_continuous(self, error_token, correction_token):
        # "(has) played" - "(has) been playing"
        # "(had) been playing" - "(had) played"
        if ((self.is_perfect(error_token) and self.is_gerund(correction_token)) or
                (self.is_gerund(error_token) and self.is_perfect(correction_token))):
            return True

        # "plays" - "is playing"
        # "(will) be playing" - "(will) play"
        if ((self.is_finite_verb(error_token) and self.is_gerund(correction_token)) or
                (self.is_gerund(error_token) and self.is_finite_verb(correction_token))):
            return True

        return False

    def check_verb_pattern(self, error_token, correction_token):
        if len(error_token['ancestor_list']):
            for a in error_token['ancestor_list']:
                ancestor = self.construction_dict[a[1]]
                # "decided announcing it" - "decide to announce it"
                # "try visiting the stadium" - "try to visit the stadium"
                if ancestor['token_lemma'] in self.infinitive_verbs and \
                        self.is_gerund(error_token) and self.is_infinitive(correction_token):
                    return True

                # "avoid to announce it" - "avoid announcing it"
                # "try to visit the stadium" - "try visiting the stadium"
                elif ancestor['token_lemma'] in self.gerund_verbs and \
                        self.is_infinitive(error_token) and self.is_gerund(correction_token):
                    return True
        return False

    def noun_adj_participle(self, error_token):
        # "materials produce in the country" - "materials produced in the country"
        # "prone to make mistakes" - "prone to making mistakes"

        if self.is_finite_verb(error_token) and len(error_token['ancestor_list']):
            # check the first ancestor of the error token
            ancestor_id = error_token['ancestor_list'][0][1]
            ancestor = self.construction_dict[ancestor_id]
            noun = ancestor['token_pos'] == 'NOUN'
            adj = ancestor['token_pos'] == 'ADJ'
            if noun or adj:
                for correction in self.full_correction.values():
                    if self.is_participle(correction):
                        return True
        return False

    def check_collective_noun(self, error_token):
        # sport programmes - sports programmes
        # Indonesians workers - Indonesian workers
        if error_token['token_pos'] == 'NOUN' and len(error_token['ancestor_list']):
            for a in error_token['ancestor_list']:
                # to check only the nearest dependent noun
                if a[1] < self.current_token_id + 2 and \
                        self.construction_dict[a[1]]['token_pos'] == 'NOUN':
                    return True
        return False

    def check_possessive(self, error_token, correction_token):
        possessive_constr_error, possessive_constr_corr = 0, 0

        apostrophe_error = "'" in error_token['token']
        apostrophe_corr = "'" in correction_token['token']

        if apostrophe_error != apostrophe_corr:
            return 1, 1

        if len(error_token['children_list']):
            for c in error_token['children_list']:
                if c[0] == 'of':
                    of = self.construction_dict[c[1]]
                    if len(of['children_list']):
                        for cc in of['children_list']:
                            child = self.construction_dict[cc[1]]
                            if child['token_pos'] == 'NOUN':
                                possessive_constr_error = 1
                                break
                    if possessive_constr_error:
                        break
        if not possessive_constr_error and len(error_token['ancestor_list']):
            for a in error_token['ancestor_list']:
                if a[0] == 'of':
                    of = self.construction_dict[a[1]]
                    if len(of['ancestor_list']):
                        for aa in of['ancestor_list']:
                            ancestor = self.construction_dict[aa[1]]
                            if ancestor['token_pos'] == 'NOUN':
                                possessive_constr_error = 1
                                break
                    if possessive_constr_error:
                        break

        if len(correction_token['children_list']):
            for c in correction_token['children_list']:
                if c[0].lower() == 'of':
                    of = self.full_correction[c[1]]
                    if len(of['children_list']):
                        for cc in of['children_list']:
                            child = self.full_correction[cc[1]]
                            if child['token_pos'] == 'NOUN':
                                possessive_constr_corr = 1
                                break
                    if possessive_constr_corr:
                        break
        if not possessive_constr_corr and len(correction_token['ancestor_list']):
            for a in correction_token['ancestor_list']:
                if a[0].lower() == 'of':
                    of = self.full_correction[a[1]]
                    if len(of['ancestor_list']):
                        for aa in of['ancestor_list']:
                            ancestor = self.full_correction[aa[1]]
                            if ancestor['token_pos'] == 'NOUN':
                                possessive_constr_corr = 1
                                break
                    if possessive_constr_corr:
                        break

        if possessive_constr_error != possessive_constr_corr:
            return 1, 0

        return 0, 0

    def check_gerund_noun(self, error_token, correction_token):
        # "attending of gym" - "attendance of gym"
        gerund_error = error_token['token'].endswith('ing')
        gerund_corr = correction_token['token'].endswith('ing')
        if gerund_error != gerund_corr:
            return True
