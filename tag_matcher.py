import logging
from dictionaries import pos_dict
from rules import Rules


class TagMatcher:
    tags = {
        # 1: "Punctuation",
        # 2: "Spelling",
        3: "Capitalisation",
        4: "Determiners",
        5: "Articles",
        6: "Quantifiers",
        7: "Verbs",
        8: "Tense",
        9: "Choice of tense",
        10: "Tense form",
        11: "Voice",
        12: "Modals",
        13: "Verb pattern",
        14: "Gerund or participle construction",
        15: "Infinitive construction",
        16: "Nouns",
        17: r"Countable\Uncountable nouns",
        18: "Prepositional noun",
        19: "Possessive form of a noun",
        20: "Noun+infinitive",
        21: "Noun number",
        22: "Prepositions",
        23: "Conjunctions",
        24: "Adjectives",
        25: "Prepositional adjective",
        26: "Adjective as collective noun",
        27: "Adverbs",
        28: "Prepositional noun",
        29: "Degree of comparison",
        30: "Numerals",
        31: "Pronouns",
        32: "Agreement",
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

    prepositional_tags = [
        18,  # Prepositional noun
        19,  # Possessive form of noun (science developing - developing of science)
        22,  # Prepositions
        25,  # Prepositional adjective
        28,  # Prepositional adverb
    ]

    def __init__(self, nlp):
        self.nlp = nlp
        self.rules = Rules()

    def token(self, error_token, tokens):
        for token_id, token in tokens.items():
            if token['token'] == error_token.lower():
                return token_id, token
        return None, None

    def update_error(self, error_record, sentence_dict):
        new_error = {}
        error = error_record['error']
        for i, error_token in enumerate(error.split()):
            token_id, token = self.token(error_token=error_token, tokens=error_record['tokens'])
            if len(token['ancestor_list']):
                for a in token['ancestor_list']:
                    if a[1] not in new_error.keys():
                        ancestor = sentence_dict[a[1]]
                        if 'idx_1' in ancestor.keys():
                            new_error[a[1]] = ancestor
            new_error[token_id] = token
            if len(token['children_list']):
                for c in token['children_list']:
                    if c[1] not in new_error.keys():
                        child = sentence_dict[c[1]]
                        if 'idx_1' in child.keys():
                            new_error[c[1]] = child

        return dict(sorted(new_error.items()))

    def update_correction(self, error_record, new_error):
        new_correction = ''
        correction_added = 0

        correction = error_record['correction']
        idx_1_orig, idx_2_orig = error_record['idx_1'], error_record['idx_2']

        for token_id, token in new_error.items():
            idx_1, idx_2 = token['idx_1'], token['idx_2']
            if idx_2 < idx_1_orig or idx_1 > idx_2_orig:
                new_correction += ' ' + token['token'] if new_correction != '' else token['token']
            elif not correction_added:
                new_correction += ' ' + correction if new_correction != '' else correction
                correction_added = True
        return new_correction

    ###################################################################################################

    def define_rules(self, token_properties, matched_tags):
        rules = []
        checked_prepositions = False
        for tag in self.prepositional_tags:
            if tag in matched_tags:
                checked_prepositions = True
                break

        pos_tag = token_properties['token_pos']
        tag = token_properties['token_tag']

        if 19 not in matched_tags and \
                ("'" in token_properties['token'] or
                 self.rules.token_in_correction(mode=12, missing=False)):
            rules.append('possessive')

        if 36 not in matched_tags and \
                (self.rules.is_negative(token_properties) or
                 self.rules.token_in_correction(mode=13, missing=False)):
            rules.append('negation')

        if 5 not in matched_tags and \
                (token_properties['token'] in self.rules.articles or
                 self.rules.token_in_correction(mode=3, missing=False)):
            rules.append('articles')

        if 31 not in matched_tags and \
                ((pos_tag == 'PRON' and tag != 'DT' and not self.rules.is_conjunction(token_properties)) or
                 self.rules.token_in_correction(mode=5, missing=False)):
            rules.append('pronouns')

        if 4 not in matched_tags and \
                ((tag == 'DT' and token_properties['token'] not in self.rules.articles) or
                 self.rules.token_in_correction(mode=9, missing=False)):
            rules.append('determiners')

        if 6 not in matched_tags and \
                (token_properties['token'] in self.rules.quantifiers or
                 self.rules.token_in_correction(mode=10, missing=False)):
            rules.append('quantifiers')

        # "that modern as" - "as modern as" / "such important as" - "as important as"
        # "twice" - "twice as many"
        # "more advantages instead of.." - "more advantages than.."
        if 37 not in matched_tags and 6 not in matched_tags and 'quantifiers' not in rules and \
                (self.rules.token_from_comparative_constr(token_properties) or
                 self.rules.token_in_correction(mode=11, missing=False)):
            rules.append('comparative_constr')

        if 29 not in matched_tags and 6 not in matched_tags and 'quantifiers' not in rules and \
                (self.rules.is_comparative(token_properties) or
                 self.rules.token_in_correction(mode=7, missing=False)):
            rules.append('comparison')

        if 30 not in matched_tags and \
                (self.rules.is_numeral(token_properties) or
                 self.rules.token_in_correction(mode=6, missing=False)):
            rules.append('numerals')

        if 34 not in matched_tags and \
                ((self.rules.token_in_error(mode=8, missing=False) and
                  self.rules.token_in_correction(mode=8, missing=True)) or
                 (self.rules.token_in_error(mode=8, missing=True) and
                  self.rules.token_in_correction(mode=8, missing=False))):
            rules.append('relative_clause')

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

        '''
        For verbs we always check agreement with subject, because checking whether we should check it or not
        basically involves the check
        '''
        if pos_tag == 'VERB' or pos_tag == 'AUX':
            if not 12 in matched_tags and self.rules.allow_check_agreement() and \
                    not (self.rules.is_participle(token_properties) or tag in self.rules.gerund):
                rules.append('agreement')

            rules.append('verbs')

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

            if pos_tag == 'VERB':
                rules.append('verb_choice')

        elif pos_tag == 'NOUN':
            rules.append('noun_number')
            rules.append('noun')

        if pos_tag in ['NOUN', 'ADJ', 'ADV']:
            rules.append('lex_choice')

        if 'verbs' in rules and 'pronouns' in rules:
            rules.remove('pronouns')

        return rules

    def apply_rule(self, rule, error_token, token_id, correction, matched_tags):
        self.rules.error_span = []
        self.rules.correction_span = ''
        self.rules.span.parameters(construction_dict=self.rules.construction_dict,
                                   correction_dict=self.rules.correction,
                                   full_correction_dict=self.rules.full_correction,
                                   error_token=error_token,
                                   token_id=self.rules.current_token_id,
                                   sentence_tokens=self.rules.sentence_tokens)
        tag = 0
        pos_tag = error_token['token_pos']

        if rule == 'possessive':
            self.rules.error_span, self.rules.correction_span = self.rules.span.possessive_span(error_token,
                                                                                                apostrophe=1)
            tag = 19  # Possessive form of noun

        elif rule == 'articles':
            tag = self.rules.check_articles(error_token)

        elif rule == 'pronouns':
            tag = self.rules.check_pronouns(error_token)

        elif rule == 'determiners':
            tag = self.rules.check_determiners(error_token)

        elif rule == 'relative_clause':
            self.rules.error_span, self.rules.correction_span = self.rules.span.relative_clause_span()
            tag = 34  # Relative clauses

        elif rule == 'quantifiers':
            tag = self.rules.check_quantifiers(error_token)

        elif rule == 'comparative_constr':
            tag = self.rules.check_comparative_construction()

        elif rule == 'comparison' and 37 not in matched_tags:
            tag = self.rules.check_comparison(error_token)

        elif rule == 'numerals':
            tag = self.rules.check_numerals(error_token)

        elif rule == 'conjunctions' and 34 not in matched_tags:
            tag = self.rules.check_conjunctions(error_token)

        elif rule == 'negation' and 36 not in matched_tags:
            tag = self.rules.check_negation(error_token)

        # "comparing with" - "compared to" is the case of Comparative construction error,
        # so if we have already detected it, we do not need to check prepositions
        elif rule == 'prepositions' and not 37 in matched_tags:
            prep_id, prep_corr = self.rules.span.token_in_correction(mode=1, missing=False)
            if len(prep_corr.keys()) and prep_corr['token'] == 'with' and 37 in matched_tags:
                return None
            tag = self.rules.check_prepositions(error_token)

        elif pos_tag == 'VERB' or pos_tag == 'AUX':
            if rule == 'agreement':
                tag = self.rules.check_agreement_subject_pred(error_token)

            elif rule == 'verbs':
                tag = self.rules.check_verb(error_token=error_token, only_check_tense=11 in matched_tags)
                if not tag:
                    tag = self.rules.check_tense_form()

            elif rule == 'modals':
                tag = self.rules.check_modals(error_token)

            elif rule == 'pattern':
                tag = self.rules.check_pattern(error_token)

            elif rule == 'verb_choice':
                tag = self.rules.check_verb_choice(error_token)

        elif pos_tag == 'NOUN':
            if rule == 'noun_number':
                tag = self.rules.check_noun_number(error_token)
            elif rule == 'noun':
                tag = self.rules.check_noun(error_token)

        # do not check lexical choice if we have detected
        # Articles, Numerals, Pronouns, Negation or Degree of comparison error
        if rule == 'lex_choice' and \
                6 not in matched_tags and 30 not in matched_tags and 31 not in matched_tags and \
                29 not in matched_tags and 36 not in matched_tags and 38 not in matched_tags:
            check_number = pos_tag in ['NOUN', 'ADJ']
            correct_number = 21 not in matched_tags
            tag = self.rules.check_lexical_choice(error_token=error_token, token_id=token_id,
                                                  check_number=check_number, correct_number=correct_number)

        if tag and self.rules.error_span == []:
            self.rules.error_span = [error_token['token'], error_token['idx_1'], error_token['idx_2']]
        if tag and self.rules.correction_span == '':
            self.rules.correction_span = correction
        return tag

    ########################################################################################################

    def match_tag(self, error_record, sentence_dict):
        match = []
        error_tags = {}
        correction_dict = {}

        try:
            self.rules.full_error = error_record
            self.rules.construction_dict = self.update_error(error_record, sentence_dict)
            self.rules.sentence_tokens = sentence_dict

            correction = self.update_correction(error_record, self.rules.construction_dict)
            self.rules.full_correction = self.nlp.spacy_sentence_dict(correction)
            for token_id, token in self.rules.full_correction.items():
                if token['token'] in error_record['correction'].split():
                    correction_dict[token_id] = token
            self.rules.correction = correction_dict

            for i, error_token in enumerate(error_record['error'].split()):
                token_id, token = self.token(error_token=error_token, tokens=error_record['tokens'])

                if token:
                    # at this point we examine each token from the error span separately
                    # if we encounter constructions like analytical predicates ('have done', 'will be doing' etc),
                    # the error will be broadened when the rule is applied
                    self.rules.error_properties = token
                    self.rules.current_token_id = token_id
                    set_of_rules = self.define_rules(token_properties=token, matched_tags=match)

                    for rule_num, rule in enumerate(set_of_rules):
                        tag = self.apply_rule(rule=rule, error_token=token,
                                              token_id=i, correction=error_record['correction'],
                                              matched_tags=match)

                        # Conflicting tags that cannot be assigned to the same construction
                        # Quantifiers (6) and Degree of comparison (29): "more modern"
                        # Relative clauses (34), Pronouns (31) and Conjunctions (23): "who", "which", "that"
                        # Possessive form of noun (20) and Prepositional noun (19): "shoes pair" - "pair of shoes"
                        # Comparative construction (37) and Choice of lexical item (40): "comparing with" - "compared to"
                        # Confusion of category (44) and Choice of lexical item (40): "sponsorship" - "sponsoring"
                        if tag:
                            if tag not in match and \
                                    not (tag == 6 and 29 in match) and \
                                    not (tag == 24 and 34 in match) and \
                                    not (tag == 31 and 23 in match) and \
                                    not (tag == 18 and 19 in match) and \
                                    not (tag == 40 and 37 in match) and \
                                    not (tag == 40 and 44 in match):
                                match.append(tag)

                                if token_id not in error_tags.keys():
                                    error_tags[token_id] = {}
                                    error_tags['sentence_id'] = error_record['sentence_id']

                                error_tags[token_id][rule_num] = {
                                    'tag': self.tags[tag],
                                    'error_span': self.rules.error_span,
                                    'correction': self.rules.correction_span,
                                }

                                if rule == 'verbs' and tag == 11:
                                    new_tag = self.apply_rule(rule=rule, error_token=token,
                                                              token_id=i, correction=error_record['correction'],
                                                              matched_tags=match)
                                    if new_tag == 9:
                                        error_tags[token_id][rule_num] = {
                                            'tag': self.tags[new_tag],
                                            'error_span': self.rules.error_span,
                                            'correction': self.rules.correction_span,
                                        }

        except Exception as exc:
            with open('logger.txt', 'w') as log:
                log.write(str(exc) + '\n\n')
                log.close()

        # for tag_id in match:
        #     error_tags.append(self.tags[tag_id])
        # tokens_with_tags[token_id] = match
        # match = []
        # return tokens_with_tags
        # return match
        return error_tags

    def get_curr_correction(self, error_token_id, full_correction):
        corr_tokens = full_correction.split()
        if len(corr_tokens) >= error_token_id:
            return corr_tokens[error_token_id]
        return ''
