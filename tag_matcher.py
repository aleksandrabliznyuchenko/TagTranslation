from rules import Rules
from dictionaries import pos_dict


class TagMatcher:
    tags = {
        # 1: "Punctuation",
        # 2: "Spelling",
        3: "Capitalisation",  ##
        4: "Determiners",  #
        5: "Articles",  ##
        6: "Quantifiers",
        7: "Verbs",  # not used ?
        8: "Tense",  # not used ?
        9: "Choice of tense",  ##
        10: "Tense form",
        11: "Voice",
        12: "Modals",  ##
        13: "Verb pattern",  ##
        14: "Gerund or participle construction",  ##
        15: "Infinitive construction",
        16: "Nouns",
        17: r"Countable\Uncountable nouns",
        18: "Prepositional noun",  ##
        19: "Possessive form of a noun",
        20: "Noun+infinitive",
        21: "Noun number",  ##
        22: "Prepositions",  ##
        23: "Conjunctions",
        24: "Adjectives",
        25: "Prepositional adjective",  ##
        26: "Adjective as collective noun",
        27: "Adverbs",
        28: "Prepositional noun",  ##
        29: "Degree of comparison",
        30: "Numerals",
        31: "Pronouns",
        32: "Agreement",  ##
        33: "Word order",
        34: "Relative clauses",
        35: "Parallel construction",
        36: "Negation",
        37: "Comparative construction",
        38: "Confusion of structures",
        39: "Word choice",
        40: "Choice of lexical item",
        41: "Change, deletion or addition of part of lexical item",
        42: "Derivation",
        43: "Formational affixes",
        44: "Confusion of category",
        45: "Compound word",
        # 46: "Referential device",
        # 47: "Coherence",
        # 48: "Linking device",
        # 49: "Inappropriate register",
        # 50: "Absence of a necessary component in clause or sentence",
        # 51: "Redundant component in clause or sentence",
        # 52: "Absence of necessary explanation or detail",
    }

    prepositional_tags = [18, 22, 25]

    def __init__(self, nlp):
        self.nlp = nlp
        self.rules = Rules()

    def token(self, error_token, tokens):
        for token_id, token in tokens.items():
            if token['token'] == error_token.lower():
                return token_id, token
        return None, None

    def find_perf_participle(self):
        if len(self.rules.full_error['tokens'].values()):
            for token in self.rules.full_error['tokens'].values():
                if self.rules.is_participle(token):
                    aspect = token['token_morph'].get('Aspect')
                    if aspect and aspect[0] == 'Perf':
                        return True
                # sometimes participles like "concerned", "encouraged" are annotated as adjectives
                if token['token_pos'] == 'ADJ' and token['token'].endswith('ed') and len(token['ancestor_list']):
                    for a in token['ancestor_list']:
                        ancestor = self.rules.sentence_dict[a[1]]
                        if ancestor['token_pos'] == 'AUX':
                            return True

        for corr_token in self.rules.correction_properties.values():
            if self.rules.is_participle(corr_token):
                aspect = corr_token['token_morph'].get('Aspect')
                if aspect and aspect[0] == 'Perf':
                    return True
            # sometimes participles like "concerned", "encouraged" are annotated as adjectives
            if corr_token['token_pos'] == 'ADJ' and corr_token['token'].endswith('ed') and \
                    len(corr_token['ancestor_list']):
                for a in corr_token['ancestor_list']:
                    ancestor = self.rules.correction_properties[a[1]]
                    if ancestor['token_pos'] == 'AUX':
                        return True

    ###################################################################################################

    def define_rules(self, token_properties, matched_tags, token_id):
        rules = []
        checked_prepositions = False
        for tag in self.prepositional_tags:
            if tag in matched_tags:
                checked_prepositions = True
                break

        pos_tag = token_properties['token_pos']
        tag = token_properties['token_tag']

        # if 'articles' not in matched_tags and \
        if 5 not in matched_tags and \
                (token_properties['token'] in ['a', 'an', 'the'] or
                 self.rules.token_in_correction(mode=3, missing=False)):
            rules.append('articles')

        # firstly, we scan the error span and the correction span for conjunctions and later for prepositions,
        # so that we only apply the rule that checks conjunctions in cases like
        # "women between 55 to 65" - "women between 55 and 65"
        if 23 not in matched_tags and \
                (self.rules.is_conjunction(token_properties) or
                 self.rules.token_in_correction(mode=4, missing=False)):
            rules.append('conjunctions')

        if not checked_prepositions and 'conjunctions' not in rules and \
                (tag in self.rules.prepositions or
                 self.rules.token_in_correction(mode=1, missing=False)):
            rules.append('prepositions')

        if 31 not in matched_tags and \
            (pos_tag == 'PRON' or self.rules.token_in_correction(mode=5, missing=False)):
            rules.append('pronouns')

        '''
        For verbs we always check agreement with subject, because checking whether we should check it or not
        basically involves the check
        '''
        if pos_tag == 'VERB' or pos_tag == 'AUX':
            if not (self.rules.is_participle(token_properties) or tag in self.rules.gerund):
                rules.append('agreement')

            rules.append('verbs')

            if 11 not in matched_tags and 9 not in matched_tags \
                    and self.find_perf_participle():
                rules.append('voice')

            if 12 not in matched_tags and \
                    (self.rules.is_modal(token_properties) or
                     self.rules.token_in_correction(mode=2, missing=False)):
                rules.append('modals')

            # cases like "carried" - "carried out" (Verb Pattern)
            if self.rules.token_in_correction(mode=1, missing=False) or \
                    self.rules.token_in_error(mode=1, missing=False):
                rules.append('pattern')
                if 'prepositions' in rules:
                    rules.remove('prepositions')

        elif pos_tag == 'NOUN':
            if tag in pos_dict['NUM']:
                rules.append('numerals')
            else:
                rules.append('noun_number')

        if 'verbs' in rules and 'pronouns' in rules:
            rules.remove('pronouns')

        return rules

    def apply_rule(self, rule, error_token, token_id_max, correction):
        tag = 0
        pos_tag = error_token['token_pos']

        # if rule not in ['agreement', 'verbs']:
        if not rule == 'agreement':
            # set new correction span if needed spaCy to work more precisely
            # for example, from 'the' to 'the number' or from 'have been' to 'have been developing'
            correction_upd = self.update_correction(correction=correction,
                                                    token_id=token_id_max,
                                                    sentence_dict=self.rules.sentence_dict)
            self.rules.correction_properties = self.nlp.spacy_sentence_dict(correction_upd)

        if rule == 'articles':
            tag = self.rules.check_articles(error_token)

        # TODO: relative clauses (and complex cases of word order errors?)
        elif rule == 'conjunctions':
            tag = self.rules.check_conjunctions(error_token)

        elif rule == 'prepositions':
            tag = self.rules.check_prepositions(error_token)

        elif rule == 'pronouns':
            tag = self.rules.check_pronouns(error_token)

        elif pos_tag == 'VERB' or pos_tag == 'AUX':
            if rule == 'agreement':
                tag = self.rules.check_agreement_subject_pred(error_token)

            elif rule == 'verbs':
                tag = self.rules.check_verb(error_token)
                if not tag:
                    tag = self.rules.check_tense_form()

            elif rule == 'voice':
                tag = self.rules.check_voice()

            elif rule == 'modals':
                tag = self.rules.check_modals(error_token)

            elif rule == 'pattern':
                tag = self.rules.check_pattern(error_token)

        elif pos_tag == 'NOUN':
            if rule == 'numerals':
                # TODO Numerals
                tag = 30  # Numerals
            elif rule == 'noun_number':
                tag = self.rules.check_noun()

        return tag

    ########################################################################################################

    # def set_correction(self, rule, correction, token_id, sentence_dict):
    #     # if rule in self.broad_correction_span:
    #     correction = self.update_correction(correction=correction,
    #                                         token_id=token_id,
    #                                         sentence_dict=sentence_dict)
    #     self.rules.correction_properties = self.nlp.spacy_sentence_dict(correction)

    def update_correction(self, correction, token_id, sentence_dict, step=1):
        if len(sentence_dict.keys()) > token_id + step:
            for s in range(1, step + 1):
                correction += ' ' + sentence_dict[token_id + s]['token']
        return correction

    def match_tag(self, error_record, sentence_dict):
        match, error_tags = [], []
        token_id_max = 0

        error = error_record['error']
        self.rules.full_error = error_record
        self.rules.sentence_dict = sentence_dict

        # TODO: overusing spaCy -- in some cases we do not need to parse the correction
        # OR need to parse a broadened version of correction
        correction = error_record['correction']
        self.rules.correction_properties = self.nlp.spacy_sentence_dict(correction)

        for key in error_record['tokens']:
            if key > token_id_max:
                token_id_max = key

        for i, error_token in enumerate(error.split()):
            token_id, token = self.token(error_token=error_token, tokens=error_record['tokens'])

            if token:
                # at this point we examine each token from the error span separately
                # if we encounter constructions like analytical predicates ('have done', 'will be doing' etc),
                # the error will be broadened when the rule is applied
                self.rules.error_properties = token
                self.rules.current_token_id = token_id
                set_of_rules = self.define_rules(token_properties=token, matched_tags=match, token_id=i)

                for rule in set_of_rules:
                    tag = self.apply_rule(rule, token, token_id_max, correction)
                    if tag and tag not in match:
                        # if we have already assigned the Choice of tense tag, we can not assign Voice error as well
                        if not (tag == 11 and 9 in match):
                            match.append(tag)

        for error_tag_id in match:
            error_tags.append(self.tags[error_tag_id])
        return error_tags
        # return match
