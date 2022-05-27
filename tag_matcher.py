import logging
from dictionaries import infinitive_verbs
from rules import Rules


class TagMatcher:
    tags = {
        # 1: "Punctuation",
        # 2: "Spelling",
        3: "Capitalisation",
        4: "Determiners",
        5: "Articles",
        6: "Quantifiers",
        # 7: "Verbs",
        # 8: "Tense",
        9: "Tense_choice",
        10: "Tense_form",
        11: "Voice",
        12: "Modals",
        13: "Verb_pattern",
        14: "Participial_constr",
        15: "Infinitive_constr",
        # 16: "Nouns",
        # 17: "Countable_uncountable",
        18: "Prepositional_noun",
        19: "Possessive",
        20: "Noun_inf",
        21: "Noun_number",
        22: "Prepositions",
        23: "Conjunctions",
        # 24: "Adjectives",
        25: "Prepositional_adjective",
        26: "Adj_as_collective",
        27: "Adverbs",
        28: "Prepositional_adv",
        29: "Comparison_degree",
        30: "Numerals",
        31: "Pronouns",
        32: "Agreement_errors",
        33: "Word_order",
        34: "Relative_clause",
        35: "Lack_par_constr",
        36: "Negation",
        37: "Comparative_constr",
        38: "Confusion_of_structures",
        39: "Word_choice",
        40: "lex_item_choice",
        41: "lex_part_choice",
        42: "Derivation",
        43: "Formational_affixes",
        44: "Category_confusion",
        45: "Compound_word",
        # 46: "Ref_device",
        # 47: "Coherence",
        # 48: "Linking_device",
        # 49: "Inappropriate_register",
        # 50: "Absence_comp_sent",
        51: "Redundant_comp",
        52: "Absence_explanation",
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
                        if ancestor['token_pos'] == 'AUX' and a[1] + 1 in sentence_dict.keys():
                            next_token = sentence_dict[a[1] + 1]
                            if self.rules.is_negative(next_token):
                                new_error[a[1] + 1] = next_token
                        elif (ancestor['token_pos'] == 'VERB' or
                              (ancestor['token_pos'] == 'ADJ' and self.rules.is_perfect(ancestor)) or
                              (ancestor['token_pos'] == 'NOUN' and self.rules.is_gerund(ancestor))) and \
                                a[1] - 1 in sentence_dict.keys():
                            prev_token = sentence_dict[a[1] - 1]
                            if prev_token['token_pos'] == 'ADV':
                                new_error[a[1] - 1] = prev_token
            new_error[token_id] = token
            if len(token['children_list']):
                for c in token['children_list']:
                    if c[1] not in new_error.keys():
                        child = sentence_dict[c[1]]
                        if 'idx_1' in child.keys():
                            new_error[c[1]] = child
                        if child['token_pos'] == 'AUX' and c[1] + 1 in sentence_dict.keys():
                            next_token = sentence_dict[c[1] + 1]
                            if self.rules.is_negative(next_token):
                                new_error[c[1] + 1] = next_token
                        elif (child['token_pos'] == 'VERB' or
                              (child['token_pos'] == 'ADJ' and self.rules.is_perfect(child)) or
                              (child['token_pos'] == 'NOUN' and self.rules.is_gerund(child))) and \
                                c[1] - 1 in sentence_dict.keys():
                            prev_token = sentence_dict[c[1] - 1]
                            if prev_token['token_pos'] == 'ADV':
                                new_error[c[1] - 1] = prev_token
            if token['token_pos'] == 'AUX' and token_id + 1 in sentence_dict.keys():
                next_token = sentence_dict[token_id + 1]
                if self.rules.is_negative(next_token):
                    new_error[token_id + 1] = next_token
            elif token['token_tag'] in self.rules.prepositions and token['token_pos'] == 'ADP':
                next_token = sentence_dict[token_id + 1]
                if next_token['token_pos'] in ['NOUN', 'PROPN']:
                    new_error[token_id + 1] = next_token
            elif (token['token_pos'] == 'VERB' or
                  (token['token_pos'] == 'ADJ' and self.rules.is_perfect(token)) or
                  (token['token_pos'] == 'NOUN' and self.rules.is_gerund(token))) and \
                    token_id - 1 in sentence_dict.keys():
                prev_token = sentence_dict[token_id - 1]
                if prev_token['token_pos'] == 'ADV':
                    new_error[token_id - 1] = prev_token
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

    def verb_in_error(self, error_token_id, sentence_dict):
        for token_id, token in sentence_dict.items():
            if token_id > error_token_id and \
                    (token['token_pos'] == 'VERB' or self.rules.is_perfect(token) or self.rules.is_gerund(token)):
                return token_id, token
        return None, None

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

        if 45 not in matched_tags and \
                ("-" in token_properties['token'] or
                 (pos_tag in ['NUM'] and self.rules.token_in_correction(mode=14, missing=False))):
            rules.append('compound')

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
                (self.rules.is_determiner(token_properties) or
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
                ((tag in self.rules.prepositions and pos_tag == 'ADP') or
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

            if not 10 in matched_tags and ((pos_tag == 'VERB' and self.rules.is_perfect(token_properties)) or
                                           token_properties['token'] == 'haves'):
                rules.append('irregular')

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

        elif pos_tag in ['NOUN', 'PROPN']:
            rules.append('noun_number')
            rules.append('noun_gerund')

        if pos_tag in ['NOUN', 'PROPN', 'ADJ', 'ADV']:
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
            tag = self.rules.check_possessive(error_token)

        if rule == 'compound':
            tag = self.rules.check_compound(error_token)

        elif rule == 'negation':
            tag = self.rules.check_negation(error_token)

        elif rule == 'articles':
            tag = self.rules.check_articles(error_token)

        elif rule == 'pronouns' and 35 not in matched_tags:
            tag = self.rules.check_pronouns(error_token)

        elif rule == 'determiners' and 35 not in matched_tags:
            tag = self.rules.check_determiners(error_token)

        elif rule == 'relative_clause':
            tag = 34  # Relative clauses

        elif rule == 'quantifiers':
            tag = self.rules.check_quantifiers(error_token)

        elif rule == 'comparative_constr':
            tag = self.rules.check_comparative_construction()

        elif rule == 'comparison' and 37 not in matched_tags:
            tag = self.rules.check_comparison(error_token)

        elif rule == 'numerals' and 45 not in matched_tags:
            tag = self.rules.check_numerals(error_token)

        elif rule == 'conjunctions' and 34 not in matched_tags:
            tag = self.rules.check_conjunctions(error_token)

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

            elif rule == 'irregular':
                tag = self.rules.check_irregular(error_token)

            elif rule == 'modals':
                tag = self.rules.check_modals(error_token)

            elif rule == 'pattern':
                tag = self.rules.check_pattern(error_token)

            elif rule == 'verb_choice':
                tag = self.rules.check_verb_choice(error_token)

        elif pos_tag in ['NOUN', 'PROPN']:
            _, correction_token = self.rules.match_correction(error_token, 1)
            if len(correction_token.keys()) != 0:
                if rule == 'noun_number':
                    tag = self.rules.check_noun_number(error_token, correction_token)
                elif rule == 'noun_gerund':
                    tag = self.rules.check_noun_gerund(error_token, correction_token)

        # do not check lexical choice if we have detected
        # Quantifiers, Numerals, Pronouns, Negation, Degree of comparison or Compound word error
        if rule == 'lex_choice' and \
                6 not in matched_tags and \
                30 not in matched_tags and 31 not in matched_tags and \
                29 not in matched_tags and 36 not in matched_tags and \
                38 not in matched_tags and 45 not in matched_tags:
            check_number = pos_tag in ['NOUN', 'PROPN', 'ADJ']
            correct_number = 21 not in matched_tags
            tag = self.rules.check_lexical_choice(error_token=error_token, token_id=token_id,
                                                  check_number=check_number, correct_number=correct_number)

        if error_token['token_pos'] == 'PROPN':
            error_token['token'] = error_token['token'].capitalize()
        if tag and self.rules.error_span == []:
            self.rules.error_span = [error_token['token'], error_token['idx_1'], error_token['idx_2']]
        if tag and self.rules.correction_span == '':
            self.rules.correction_span = correction

        if self.rules.correction_span.istitle():
            self.rules.error_span[0] = self.rules.error_span[0].capitalize()
        return tag

    ########################################################################################################

    def match_tag(self, error_record, sentence_dict):
        match = []
        error_tags = {}
        correction_dict = {}
        last_error_id = 0

        if error_record['correction'] == 'Delete':
            tag = None
            error_text = ''
            idx_1, idx_2 = 0, 0

            for i, error_token in enumerate(error_record['error'].split()):
                token_id, token = self.token(error_token=error_token, tokens=error_record['tokens'])

                if token and token['token_pos'] not in ['PUNCT', 'SENT']:
                    if token['token'].lower() in self.rules.articles:
                        tag = self.apply_rule(rule='articles', error_token=token, token_id=i,
                                              correction=error_record['correction'], matched_tags=match)
                    elif token['token'].lower() == 'to':
                        if token_id + 1 in sentence_dict.keys():
                            next_token = sentence_dict[token_id + 1]
                            if next_token['token_pos'] in ['VERB', 'AUX']:
                                for sent_token_id, sent_token in sentence_dict.items():
                                    if sent_token_id >= token_id - 5 and \
                                            sent_token['token_pos'] in ['VERB', 'AUX'] and \
                                            not self.rules.is_gerund(sent_token):
                                        tag = 13  # Verb pattern
                                        break
                                if not tag and self.rules.is_gerund(next_token):
                                    tag = 14  # Gerund or participle construction
                                if tag:
                                    self.rules.error_span = [
                                        token['token'] + ' ' + next_token['token'],
                                        token['idx_1'], next_token['idx_2']
                                    ]
                                    self.rules.correction_span = next_token['token']
                            else:
                                if error_text == '':
                                    idx_1 = token['idx_1']
                                error_text += ' ' + token['token'] if error_text != '' else token['token']
                                idx_2 = token['idx_2'] if token['idx_2'] > idx_2 else idx_2
                    else:
                        if error_text == '':
                            idx_1 = token['idx_1']
                        if token['token_pos'] == 'PROPN':
                            token['token'] = token['token'].capitalize()
                        error_text += ' ' + token['token'] if error_text != '' else token['token']
                        idx_2 = token['idx_2'] if token['idx_2'] > idx_2 else idx_2

                if tag:
                    if token_id not in error_tags.keys():
                        error_tags[token_id] = {}
                        error_tags['sentence_id'] = error_record['sentence_id']

                    error_tags[token_id][0] = {
                        'tag': self.tags[tag],
                        'error_span': self.rules.error_span,
                        'correction': self.rules.correction_span,
                    }

            # redundant element in clause or sentence
            if error_text:
                key = 0 if not len(error_tags.keys()) else list(error_tags.keys())[-1] + 1
                error_tags[key] = {}
                error_tags['sentence_id'] = error_record['sentence_id']
                error_tags[key][0] = {
                    'tag': self.tags[51],
                    'error_span': [error_text, idx_1, idx_2],
                    'correction': '',
                }
            return error_tags

        if not len(error_record['tokens'].keys()):
            return {}

        self.rules.full_error = error_record
        self.rules.sentence_tokens = sentence_dict
        self.rules.construction_dict = self.update_error(error_record, sentence_dict)

        correction = self.update_correction(error_record, self.rules.construction_dict)
        self.rules.full_correction = self.nlp.spacy_sentence_dict(correction)
        for token_id, token in self.rules.full_correction.items():
            if token['token'] in error_record['correction'].split():
                correction_dict[token_id] = token
        if not len(correction_dict.keys()) and "'" in error_record['correction']:
            for token_id, token in self.rules.full_correction.items():
                if token['token'] in error_record['correction'].split("'"):
                    correction_dict[token_id] = token
                    if token_id + 1 in self.rules.full_correction.keys():
                        correction_dict[token_id + 1] = self.rules.full_correction[token_id + 1]
                    break
        self.rules.correction = correction_dict

        for i, error_token in enumerate(error_record['error'].split()):
            token_id, token = self.token(error_token=error_token, tokens=error_record['tokens'])
            last_error_id = token_id

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
                    # Possessive form of noun (19) and Adj as collective noun (26): "people health" - "people's health"
                    # Comparative construction (37) and Choice of lexical item (40): "comparing with" - "compared to"
                    # Confusion of category (44) and Choice of lexical item (40): "sponsorship" - "sponsoring"
                    if tag:
                        if tag not in match and \
                                not (tag == 6 and 29 in match) and \
                                not (tag == 23 and 34 in match) and \
                                not (tag == 31 and 23 in match) and \
                                not (tag == 26 and 19 in match) and \
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
                                    error_tags[token_id][rule_num + 1] = {
                                        'tag': self.tags[new_tag],
                                        'error_span': self.rules.error_span,
                                        'correction': self.rules.correction_span,
                                    }

        # for cases like "who never watched" - "who has never watched"
        # we also have to examine the tokens from correction that are missing in the error span
        if len(self.rules.correction.keys()) > len(error_record['error'].split()):
            for token_id, token in self.rules.correction.items():
                error_id, error_token = self.token(error_token=token['token'], tokens=error_record['tokens'])
                if not error_token:
                    error_id, error_token = self.token(error_token=token['token_lemma'],
                                                       tokens=error_record['tokens'])
                if not error_token and not ((self.rules.is_gerund(token) or
                                             token['token_pos'] in ['NOUN', 'PROPN']) and 44 in match) \
                        and not (token['token_pos'] in ['NOUN', 'ADJ'] and 26 in match) \
                        and not (token['token'] == 'as' and 37 in match):
                    if token['token_pos'] in ['VERB', 'AUX'] or token['token'] == 'to':
                        error_verb_id, error_verb = self.verb_in_error(last_error_id, sentence_dict)
                        if error_verb:
                            self.rules.current_token_id = error_verb_id
                            self.rules.span.current_token_id = error_verb_id

                            # "started" - "has started" (Choice of tense)
                            # "started" - "has been started" (Choice of tense + Voice)
                            if self.rules.is_perfect(error_verb) and token['token_lemma'] == 'have':
                                self.rules.error_span, self.rules.correction_span = \
                                    self.rules.span.verb_span(error_verb)
                                error_tags[last_error_id + 1] = {}
                                error_tags['sentence_id'] = error_record['sentence_id']

                                # Voice
                                if token_id + 1 in self.rules.correction.keys():
                                    next_corr_token = self.rules.correction[token_id + 1]
                                    if self.rules.is_participle(next_corr_token):
                                        tense = next_corr_token['token_morph'].get('Tense')
                                        if tense and tense[0] == 'Past' and next_corr_token['token_lemma'] == 'be':
                                            error_tags[last_error_id + 1][0] = {
                                                'tag': self.tags[11],
                                                'error_span': self.rules.error_span,
                                                'correction': self.rules.correction_span,
                                            }
                                            # Choice of tense
                                            error_tags[last_error_id + 1][1] = {
                                                'tag': self.tags[9],
                                                'error_span': self.rules.error_span,
                                                'correction': self.rules.correction_span,
                                            }
                                            break

                                # Choice of tense
                                error_tags[last_error_id + 1][0] = {
                                    'tag': self.tags[9],
                                    'error_span': self.rules.error_span,
                                    'correction': self.rules.correction_span,
                                }
                            # "making" - "is making" / "was making" / "has been making" / "will be making" (Tense form)
                            elif self.rules.is_gerund(error_verb) and token['token_lemma'] == 'be':
                                self.rules.error_span, self.rules.correction_span = \
                                    self.rules.span.verb_span(error_verb)
                                error_tags[last_error_id + 1] = {}
                                error_tags['sentence_id'] = error_record['sentence_id']

                                error_tags[last_error_id + 1][0] = {
                                    'tag': self.tags[10],
                                    'error_span': self.rules.error_span,
                                    'correction': self.rules.correction_span,
                                }
                            # "started" - "is started" / "was started" / "could be started" (Voice)
                            elif self.rules.is_perfect(error_verb) and token['token_lemma'] == 'be':
                                self.rules.error_span, self.rules.correction_span = \
                                    self.rules.span.verb_span(error_verb)
                                error_tags[last_error_id + 1] = {}
                                error_tags['sentence_id'] = error_record['sentence_id']

                                error_tags[last_error_id + 1][0] = {
                                    'tag': self.tags[11],
                                    'error_span': self.rules.error_span,
                                    'correction': self.rules.correction_span,
                                }
                            # "start" - "could start" / "should start" / "may start"
                            elif self.rules.is_modal(token):
                                self.rules.error_span, self.rules.correction_span = \
                                    self.rules.span.modals_span(error_token=error_verb, modal_error=0)
                                error_tags[last_error_id + 1] = {}
                                error_tags['sentence_id'] = error_record['sentence_id']

                                error_tags[last_error_id + 1][0] = {
                                    'tag': self.tags[12],
                                    'error_span': self.rules.error_span,
                                    'correction': self.rules.correction_span,
                                }
                            # "prove" - "to prove" (Verb pattern or Infinitive construction)
                            elif self.rules.is_finite_verb(error_verb) and token['token'] == 'to':
                                self.rules.error_span, self.rules.correction_span = \
                                    self.rules.span.gerund_part_inf_span(error_verb)
                                error_tags[last_error_id + 1] = {}
                                error_tags['sentence_id'] = error_record['sentence_id']

                                # Verb pattern
                                if error_verb_id - 1 in sentence_dict.keys():
                                    prev_token = sentence_dict[error_verb_id - 1]
                                    if prev_token['token_pos'] in ['VERB', 'AUX'] and \
                                            prev_token['token_lemma'] in infinitive_verbs:
                                        error_tags[last_error_id + 1][0] = {
                                            'tag': self.tags[13],
                                            'error_span': self.rules.error_span,
                                            'correction': self.rules.correction_span,
                                        }
                                        break
                                # Infinitive construction
                                error_tags[last_error_id + 1][0] = {
                                    'tag': self.tags[15],
                                    'error_span': self.rules.error_span,
                                    'correction': self.rules.correction_span,
                                }
                        elif token['token'] == 'to' and len(token['children_list']):
                            for c in token['children_list']:
                                child = self.rules.full_correction[c[1]]
                                if child['token_pos'] in ['NOUN', 'PROPN']:
                                    error_noun_id, error_noun = self.rules.span.match_error_token(child, c[1],
                                                                                                  mode=1)
                                    if len(error_noun.keys()):
                                        self.rules.error_span = [error_noun['token'],
                                                                 error_noun['idx_1'], error_noun['idx_2']]
                                    self.rules.correction_span = token['token'] + ' ' + error_noun['token']
                                    # Prepositions
                                    error_tags[last_error_id + 1] = {}
                                    error_tags['sentence_id'] = error_record['sentence_id']
                                    error_tags[last_error_id + 1][0] = {
                                        'tag': self.tags[22],
                                        'error_span': self.rules.error_span,
                                        'correction': self.rules.correction_span,
                                    }
                                    break

                    # absence of a necessary explanation or detail
                    elif token['token_pos'] in ['ADJ', 'ADV', 'NOUN', 'PROPN'] and token['token_lemma'] != 'of':
                        absent_token = 1
                        if 40 in match:
                            absent_token = 0
                            for tag_token_id, tag_set in error_tags.items():
                                if type(tag_set) == dict:
                                    for key, value in tag_set.items():
                                        cur_token = self.rules.sentence_tokens[tag_token_id]
                                        if value['tag'] == 'lex_item_choice' and \
                                                cur_token['token_pos'] in ['ADJ', 'ADV', 'NOUN', 'PROPN'] and \
                                                cur_token['token_pos'] != token['token_pos'] and not \
                                                (cur_token['token_pos'] in ['NOUN', 'PROPN'] and
                                                 token['token_pos'] in ['NOUN', 'PROPN']):
                                            absent_token = 1
                                            break
                                if absent_token:
                                    break

                        if absent_token:
                            idx_1, idx_2 = 0, 0
                            first_token = 1
                            for i, error_token in enumerate(error_record['error'].split()):
                                token_id, token = self.token(error_token=error_token, tokens=error_record['tokens'])
                                if token:
                                    if first_token:
                                        idx_1 = token['idx_1']
                                        first_token = 0
                                    idx_2 = token['idx_2']

                            # absence of necessary explanation or detail
                            error_tags[last_error_id + 1] = {}
                            error_tags['sentence_id'] = error_record['sentence_id']

                            error_tags[last_error_id + 1][0] = {
                                'tag': self.tags[52],
                                'error_span': [error_record['error'], idx_1, idx_2],
                                'correction': error_record['correction'],
                            }
                            break

        if len(error_tags.keys()):
            error_tags = self.update_correction_span(error_tags)

        return error_tags

    def update_correction_span(self, error_tags):
        for error_id, tags in error_tags.items():
            if type(tags) is dict:
                for tag_id, tag in tags.items():
                    if tag['tag'] in ['lex_item_choice', 'Category_confusion'] and \
                            len(tag['correction'].split()) == 1:
                        for tag_id_upd, tag_upd in tags.items():
                            if tag_id_upd != tag_id:
                                for token in tag_upd['correction'].split():
                                    if tag['error_span'][0] == token:
                                        tag_upd['correction'] = tag_upd['correction'].replace(token, tag['correction'])
                        break
        return error_tags

    def get_curr_correction(self, error_token_id, full_correction):
        corr_tokens = full_correction.split()
        if len(corr_tokens) >= error_token_id:
            return corr_tokens[error_token_id]
        return ''
