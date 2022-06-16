import re

from dictionaries import irregular_verbs, pos_dict, \
    prepositional_nouns, prepositional_adj, prepositional_adv
from rules_base import RulesBase
from error_span import ErrorSpan


class Rules(RulesBase):

    def __init__(self):
        super(Rules, self).__init__()
        self.span = ErrorSpan()

    """
    Rules that return tag matches
    
    Grammatical change, addition or deletion of a lexical item
    """

    def check_articles(self, error_token):
        # "a number" - "the number"
        # "number of the girls" - "number of girls"
        # "choose good film" - "choose a good film"

        if error_token['token'] in self.articles:
            corr_id, correction_match = self.match_correction(error_token, mode=1)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                self.error_span, self.correction_span = self.span.articles_span(
                    [self.current_token_id, error_token],
                    [corr_id, correction_match]
                )
                return 5  # Articles
            elif self.token_in_correction(mode=3, missing=True):
                self.error_span, self.correction_span = self.span.articles_span(
                    [self.current_token_id, error_token], []
                )
                # "few" - "a few" / "a fewer" - "fewer"
                if error_token['token'].lower() == 'a' and len(error_token['ancestor_list']):
                    for a in error_token['ancestor_list']:
                        if a[1] in self.construction_dict.keys():
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token'] in self.quantifiers:
                                return 6  # Quantifiers
                return 5  # Articles
        else:
            article_id, article_token = self.token_in_error_token(mode=3)
            if len(article_token.keys()):
                corr_id, correction_match = self.match_correction(article_token, mode=1)
                if correction_match and correction_match['token'].lower() != article_token['token']:
                    self.span.current_token_id = article_id
                    self.error_span, self.correction_span = self.span.articles_span(
                        [article_id, article_token],
                        [corr_id, correction_match]
                    )
                    return 5  # Articles
                elif self.token_in_correction(mode=3, missing=True):
                    self.span.current_token_id = article_id
                    self.error_span, self.correction_span = self.span.articles_span(
                        [article_id, article_token], []
                    )
                    # "few" - "a few" / "a fewer" - "fewer"
                    if article_token['token'].lower() == 'a' and len(article_token['ancestor_list']):
                        for a in article_token['ancestor_list']:
                            if a[1] in self.construction_dict.keys():
                                ancestor = self.construction_dict[a[1]]
                                if ancestor['token'] in self.quantifiers:
                                    return 6  # Quantifiers
                    return 5  # Articles

            article_id, article = self.span.token_in_correction(mode=3)
            if len(article.keys()) and not len(article_token.keys()):
                # "more independent" - "the most independent" -- this case will be annotated later on
                if article['token'].lower() == 'the' and len(article['ancestor_list']):
                    for a in article['ancestor_list']:
                        if a[1] in self.construction_dict.keys():
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token_pos'] in ['ADJ', 'ADV'] and len(ancestor['children_list']):
                                for c in ancestor['children_list']:
                                    if c[0] == 'most':
                                        return None

                # "few" - "a few" / "a fewer" - "fewer"
                if article['token'].lower() == 'a' and len(article['ancestor_list']):
                    for a in article['ancestor_list']:
                        if a[1] in self.construction_dict.keys():
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token'] in self.quantifiers:
                                return 6  # Quantifiers

                self.error_span, self.correction_span = self.span.articles_span(
                    [], [article_id, article]
                )
                return 5  # Articles

    def check_pronouns(self, error_token):
        if error_token['token_pos'] == 'PRON':
            _, correction_match = self.match_correction(error_token, 1)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                if correction_match['token'].lower() in self.relative_conj:
                    return 34  # Relative clauses
                # "there is a sign" - "it is a sign" is a case of Confusion of structures error
                if (error_token['token'] == 'there' and correction_match['token'].lower() == 'it') or \
                        (error_token['token'] == 'it' and correction_match['token'].lower() == 'there'):
                    return 38  # Confusion of structures
                self.correction_span = correction_match['token']
                return 31  # Pronouns
            elif self.token_in_correction(mode=5, missing=True):
                self.correction_span = self.full_error['correction']
                return 31  # Pronouns
        else:
            pron_id, pronoun = self.span.token_in_correction(mode=5, missing=False)
            if len(pronoun.keys()) and self.token_in_error(mode=5, missing=True):
                self.correction_span = self.full_error['correction']
                return 31  # Pronouns

    def check_determiners(self, error_token):
        if self.is_determiner(error_token):
            _, correction_match = self.match_correction(error_token, 9)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                # "this glasses" - "these glasses" is a case of Agreement error
                error_number = error_token['token_morph'].get('Number')
                corr_number = correction_match['token_morph'].get('Number')
                if error_number and corr_number and error_number[0] != corr_number[0] and \
                        error_token['token_head'] in self.construction_dict.keys():
                    error_head_number = self.construction_dict[error_token['token_head']]['token_morph'].get('Number')
                    if error_head_number and error_head_number[0] != corr_number[0]:
                        self.correction_span = correction_match['token']
                        return 32  # Agreement
                self.correction_span = correction_match['token']
                return 4  # Determiners
            elif self.token_in_correction(mode=9, missing=True):
                return 4  # Determiners
        else:
            corr_id, corr_token = self.span.token_in_correction(mode=9, missing=False)
            if len(corr_token.keys()) and self.token_in_error(mode=9, missing=True):
                self.correction_span = corr_token['token']
                return 4  # Determiners

    def check_quantifiers(self, error_token):
        # "twice" - "twice as many"
        # "less than that" - "more than that"
        tag = self.check_comparative_construction()
        if tag:
            return tag

        # "more deep" - "deeper"
        # "more independent" - "the most independent"
        tag = self.check_comparison(error_token)
        if tag:
            return tag

        # "much space" - "more space"
        # "less benefits" - "fewer benefits"
        # "much money" - "a lot of money"
        if error_token['token'] in self.quantifiers:
            _, correction_match = self.match_correction(error_token, 10)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                self.correction_span = correction_match['token']
                return 6  # Quantifiers
            elif self.token_in_correction(mode=10, missing=True):
                return 6  # Quantifiers
        else:
            corr_id, corr_token = self.span.token_in_correction(mode=10, missing=False)
            if len(corr_token.keys()) and self.token_in_error(mode=10, missing=True):
                self.correction_span = corr_token['token']
                return 6  # Quantifiers

    def check_modals(self, error_token):
        # "can allow" - "might allow"
        # "I rather agree" - "I would rather agree"

        if self.is_modal(error_token):
            _, correction_match = self.match_correction(error_token, 4)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                self.error_span, self.correction_span = self.span.modals_span(error_token)
                return 12  # Modals
            elif self.token_in_correction(mode=2, missing=True):
                self.error_span, self.correction_span = self.span.modals_span(error_token)
                return 12
        else:
            corr_id, corr_token = self.span.token_in_correction(mode=2, missing=False)
            if len(corr_token.keys()) and self.token_in_error(mode=2, missing=True):
                self.correction_span = corr_token['token']
                return 12  # Modals

    def check_prepositions(self, error_token):
        # if the preposition is determined by the noun, the tag Prepositional noun is chosen;
        # if the preposition is determined by the adjective, the tag Prepositional adjective is chosen;
        # if the preposition is determined by the adverb, the tag Prepositional adverb is chosen;
        # in other cases the preposition is independent and tag Prepositions is chosen
        #
        # "increase of" - "increase in" (Prepositional noun)
        # "responsible of his actions" - "responsible for his actions" (Prepositional adjective)
        # "except" - "except for" (Prepositional adverb)
        # "the growth increased for this period" - "the growth increased during this period" (Prepositions)

        if error_token['token_tag'] in self.prepositions and error_token['token_pos'] == 'ADP':
            corr_id, correction_match = self.match_correction(error_token, 1)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                if len(error_token['children_list']) and error_token['token'] != 'down':
                    for c in error_token['children_list']:
                        if c[1] in self.construction_dict.keys():
                            child = self.construction_dict[c[1]]
                            # if child['token_pos'] in ['NOUN', 'PROPN'] or self.is_gerund(child):
                            # if child['token_lemma'] in prepositional_nouns.keys():
                            #     prep_noun = prepositional_nouns[child['token_lemma']]
                            #     if (type(prep_noun) != str and correction_match['token'].lower() in prep_noun) or \
                            #             prep_noun == correction_match['token'].lower():
                            #         self.error_span, self.correction_span = self.span.prepositions_span(
                            #             [self.current_token_id, error_token],
                            #             [corr_id, correction_match], 18
                            #         )
                            #         return 18  # Prepositional noun

                            # "for borrowing or buying" - "for borrowing or for buying"
                            # we look for a similar prepositional construction in the previous context
                            if self.is_gerund(child) and len(child['ancestor_list']):
                                for a in child['ancestor_list']:
                                    if a[1] != self.current_token_id and a[0] == correction_match['token']:
                                        ancestor = self.sentence_tokens[a[1]]
                                        if len(ancestor['children_list']):
                                            for cc in ancestor['children_list']:
                                                child_child = self.sentence_tokens[cc[1]]
                                                if self.is_gerund(child_child) and cc[1] != c[1]:
                                                    self.error_span, self.correction_span = \
                                                        self.span.prepositions_span(
                                                            [self.current_token_id, error_token],
                                                            [corr_id, correction_match], 35
                                                        )
                                                    return 35  # Parallel constructions
                if len(error_token['ancestor_list']):
                    for a in error_token['ancestor_list']:
                        if a[1] in self.construction_dict.keys():
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token_pos'] == 'NOUN' and ancestor['token_lemma'] in prepositional_nouns:
                                prep_noun = prepositional_nouns[ancestor['token_lemma']]
                                if (type(prep_noun) != str and correction_match['token'].lower() in prep_noun) or \
                                        prep_noun == correction_match['token'].lower():
                                    self.error_span, self.correction_span = self.span.prepositions_span(
                                        [self.current_token_id, error_token],
                                        [corr_id, correction_match], 18
                                    )
                                    return 18  # Prepositional noun
                            elif ancestor['token_pos'] == 'ADJ' and ancestor['token_lemma'] in prepositional_adj:
                                prep_adj = prepositional_adj[ancestor['token_lemma']]
                                if (type(prep_adj) != str and correction_match['token'].lower() in prep_adj) or \
                                        prep_adj == correction_match['token'].lower():
                                    self.error_span, self.correction_span = self.span.prepositions_span(
                                        [self.current_token_id, error_token],
                                        [corr_id, correction_match], 25
                                    )
                                    return 25  # Prepositional adjective
                            elif (ancestor['token_pos'] == 'ADV' or
                                  (ancestor['token_pos'] == 'ADP' and ancestor['token_tag'] == 'IN')) and \
                                    ancestor['token_lemma'] in prepositional_adv:
                                prep_adv = prepositional_adv[ancestor['token_lemma']]
                                if prep_adv == correction_match['token'].lower():
                                    self.error_span, self.correction_span = self.span.prepositions_span(
                                        [self.current_token_id, error_token],
                                        [corr_id, correction_match], 28
                                    )
                                    return 28  # Prepositional adverb
                self.error_span, self.correction_span = self.span.prepositions_span(
                    [self.current_token_id, error_token],
                    [corr_id, correction_match], 22
                )
                return 22  # Prepositions
            else:
                prep_id, preposition = self.span.token_in_correction(mode=1, missing=False)
                if not len(preposition.keys()):
                    self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                    self.correction_span = self.full_error['correction']
                    return 22  # Prepositions
        else:
            # cases when there are redundant tokens in the error span as well as prepositions
            # "be part of every person" - "be for every person"
            error_prep_id, error_prep = self.token_in_error_token(mode=1)
            if len(error_prep.keys()):
                corr_id, correction_match = self.match_correction(error_prep, 1)
                # "around" and similar words can be distinguished as adverbs and as prepositions
                # and have different tags in error and correction spans
                # due to that the rule might detect redundant errors
                # so we have to make sure that the system does not to make false matches
                if len(correction_match.keys()) and error_token['token_lemma'] != correction_match['token_lemma'] and \
                        correction_match and correction_match['token'].lower() != error_prep['token']:
                    if len(error_prep['children_list']) and error_prep['token'] != 'down':
                        for c in error_prep['children_list']:
                            if c[1] in self.construction_dict.keys():
                                child = self.construction_dict[c[1]]
                                # if child['token_pos'] in ['NOUN', 'PROPN'] or self.is_gerund(child):
                                #     if child['token_lemma'] in prepositional_nouns.keys():
                                #         prep_noun = prepositional_nouns[child['token_lemma']]
                                #         if (type(prep_noun) != str and correction_match[
                                #             'token'].lower() in prep_noun) or \
                                #                 prep_noun == correction_match['token'].lower():
                                #             self.span.current_token_id = error_prep_id
                                #             self.error_span, self.correction_span = self.span.prepositions_span(
                                #                 [error_prep_id, error_prep],
                                #                 [corr_id, correction_match], 18
                                #             )
                                #             return 18  # Prepositional noun

                                # "for borrowing or buying" - "for borrowing or for buying"
                                # we look for a similar prepositional construction in the previous context
                                if self.is_gerund(child) and len(child['ancestor_list']):
                                    for a in child['ancestor_list']:
                                        if a[1] != error_prep_id and a[0] == correction_match['token']:
                                            ancestor = self.sentence_tokens[a[1]]
                                            if len(ancestor['children_list']):
                                                for cc in ancestor['children_list']:
                                                    child_child = self.sentence_tokens[cc[1]]
                                                    if self.is_gerund(child_child) and cc[1] != c[1]:
                                                        self.span.current_token_id = error_prep_id
                                                        self.error_span, self.correction_span = \
                                                            self.span.prepositions_span(
                                                                [error_prep_id, error_prep],
                                                                [corr_id, correction_match], 35
                                                            )
                                                        return 35  # Parallel constructions
                    if len(error_prep['ancestor_list']):
                        for a in error_prep['ancestor_list']:
                            if a[1] in self.construction_dict.keys():
                                ancestor = self.construction_dict[a[1]]
                                if ancestor['token_pos'] == 'NOUN' and ancestor['token_lemma'] in prepositional_nouns:
                                    prep_noun = prepositional_nouns[ancestor['token_lemma']]
                                    if (type(prep_noun) != str and correction_match['token'].lower() in prep_noun) or \
                                            prep_noun == correction_match['token'].lower():
                                        self.error_span, self.correction_span = self.span.prepositions_span(
                                            [self.current_token_id, error_token],
                                            [corr_id, correction_match], 18
                                        )
                                        return 18  # Prepositional noun
                                elif ancestor['token_pos'] == 'ADJ' and ancestor['token_lemma'] in prepositional_adj:
                                    prep_adj = prepositional_adj[ancestor['token_lemma']]
                                    if (type(prep_adj) != str and correction_match['token'].lower() in prep_adj) or \
                                            prep_adj == correction_match['token'].lower():
                                        self.span.current_token_id = error_prep_id
                                        self.error_span, self.correction_span = self.span.prepositions_span(
                                            [error_prep_id, error_prep],
                                            [corr_id, correction_match], 25
                                        )
                                        return 25  # Prepositional adjective
                                elif (ancestor['token_pos'] == 'ADV' or
                                      (ancestor['token_pos'] == 'ADP' and ancestor['token_tag'] == 'IN')) and \
                                        ancestor['token_lemma'] in prepositional_adv:
                                    prep_adv = prepositional_adv[ancestor['token_lemma']]
                                    if prep_adv == correction_match['token'].lower():
                                        self.error_span, self.correction_span = self.span.prepositions_span(
                                            [error_prep_id, error_prep],
                                            [corr_id, correction_match], 28
                                        )
                                        return 28  # Prepositional adverb
                    self.span.current_token_id = error_prep_id
                    self.error_span, self.correction_span = self.span.prepositions_span(
                        [error_prep_id, error_prep],
                        [corr_id, correction_match], 22
                    )
                    return 22  # Prepositions
                elif not len(correction_match.keys()):
                    self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                    self.correction_span = self.full_error['correction']
                    return 22  # Prepositions
            else:
                prep_id, preposition = self.span.token_in_correction(mode=1, missing=False, missing_in_error=True)
                # "around" and similar words can be distinguished as adverbs and as prepositions
                # and have different tags in error and correction spans
                # due to that the rule might detect redundant errors
                # so we have to make sure that the system does not to make false matches
                if len(preposition.keys()) and error_token['token_lemma'] != preposition['token_lemma']:
                    if len(preposition['ancestor_list']):
                        for a in preposition['ancestor_list']:
                            ancestor = self.full_correction[a[1]]
                            if ancestor['token_pos'] in ['NOUN', 'PROPN'] or self.is_gerund(ancestor):
                                # "waste time" - "waste of time" is a Confusion of structures error
                                if preposition['token_lemma'] == 'of' and \
                                        (error_token['token_pos'] in ['NOUN', 'PROPN'] or self.is_gerund(error_token) or
                                         self.is_determiner(error_token)) and \
                                        self.check_confusion_structures(error_token, ancestor):
                                    self.error_span, self.correction_span = self.span.prepositions_span(
                                        [self.current_token_id, error_token], [prep_id, preposition], 38
                                    )
                                    return 38  # Confusion of structures
                                if ancestor['token_lemma'] in prepositional_nouns.keys():
                                    prep_noun = prepositional_nouns[ancestor['token_lemma']]
                                    if (type(prep_noun) != str and preposition['token'].lower() in prep_noun) or \
                                            prep_noun == preposition['token'].lower():
                                        self.error_span, self.correction_span = self.span.prepositions_span(
                                            [], [prep_id, preposition], 18
                                        )
                                        return 18  # Prepositional noun
                            elif ancestor['token_pos'] == 'ADJ' and ancestor['token_lemma'] in prepositional_adj:
                                prep_adj = prepositional_adj[ancestor['token_lemma']]
                                if (type(prep_adj) != str and preposition['token'].lower() in prep_adj) or \
                                        prep_adj == preposition['token'].lower():
                                    self.error_span, self.correction_span = self.span.prepositions_span(
                                        [], [prep_id, preposition], 25
                                    )
                                    return 25  # Prepositional adjective
                            elif (ancestor['token_pos'] == 'ADV' or
                                  (ancestor['token_pos'] == 'ADP' and ancestor['token_tag'] == 'IN')) and \
                                    ancestor['token_lemma'] in prepositional_adv:
                                prep_adv = prepositional_adv[ancestor['token_lemma']]
                                if prep_adv == preposition['token'].lower():
                                    self.error_span, self.correction_span = self.span.prepositions_span(
                                        [], [prep_id, preposition], 28
                                    )
                                    return 28  # Prepositional adverb
                    if len(preposition['children_list']) and preposition['token'] != 'down':
                        for c in preposition['children_list']:
                            child = self.full_correction[c[1]]
                            # if child['token_pos'] in ['NOUN', 'PROPN'] or self.is_gerund(child):
                            #     if child['token_lemma'] in prepositional_nouns.keys():
                            #         prep_noun = prepositional_nouns[child['token_lemma']]
                            #         if (type(prep_noun) != str and preposition['token'].lower() in prep_noun) or \
                            #                 prep_noun == preposition['token'].lower():
                            #             self.error_span, self.correction_span = self.span.prepositions_span(
                            #                 [], [prep_id, preposition], 18
                            #             )
                            #             return 18  # Prepositional noun
                            
                            # "for borrowing or buying" - "for borrowing or for buying"
                            # we look for a similar prepositional construction in the previous context
                            if self.is_gerund(child) and len(child['ancestor_list']):
                                for a in child['ancestor_list']:
                                    if a[1] != prep_id and a[0] == preposition['token']:
                                        ancestor = self.full_correction[a[1]]
                                        if len(ancestor['children_list']):
                                            for cc in ancestor['children_list']:
                                                child_child = self.full_correction[cc[1]]
                                                if self.is_gerund(child_child) and cc[1] != c[1]:
                                                    self.error_span, self.correction_span = \
                                                        self.span.prepositions_span(
                                                            [], [prep_id, preposition], 35
                                                        )
                                                    return 35  # Parallel constructions
                    self.correction_span = error_token['token'] + ' ' + preposition['token']
                    return 22  # Prepositions

    def check_conjunctions(self, error_token):
        # "That stands out is that..." - "What stands out is that..."
        # "women between 55 to 65" - "women between 55 and 65"
        # "it is up to everybody to decide whether which side should they take" - "it is up to everybody to decide which side should they take"
        if self.is_conjunction(error_token):
            _, correction_match = self.match_correction(error_token, 5)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                if correction_match['token'].lower() in self.relative_conj:
                    self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                    self.correction_span = correction_match['token']
                    return 34  # Relative clauses
                return 23  # Conjunctions
            elif correction_match and self.token_in_correction(mode=4, missing=True):
                return 23  # Conjunctions
        else:
            _, corr_token = self.span.token_in_correction(mode=4, missing=False)
            if corr_token and self.token_in_error(mode=4, missing=True):
                if corr_token['token'].lower() in self.relative_conj:
                    self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                    self.correction_span = corr_token['token']
                    return 34  # Relative clauses
                return 23  # Conjunctions

    def check_negation(self, error_token):
        if self.is_negative(error_token):
            corr_id, correction_match = self.match_correction(error_token, mode=13)
            if not correction_match:
                corr_id, correction_match = self.match_correction(error_token, mode=1)
            if correction_match:
                if correction_match['token'].lower() != error_token['token']:
                    self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                    return 36  # Negation
                # "need not" - "do not need"
                elif error_token['token'] == 'not' and \
                        self.current_token_id - 1 in self.sentence_tokens.keys() and \
                        corr_id - 1 in self.full_correction.keys():
                    prev_token_error = self.sentence_tokens[self.current_token_id - 1]
                    prev_token_corr = self.full_correction[corr_id - 1]
                    if prev_token_error['token_lemma'] != 'do' and prev_token_corr['token_lemma'] == 'do':
                        self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                        return 36  # Negation
            elif correction_match and self.token_in_correction(mode=13, missing=True):
                self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                return 36  # Negation
        elif self.token_in_correction(mode=13, missing=False) and self.token_in_error(mode=13, missing=True):
            self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
            return 36  # Negation

    '''
    Verbal rules
    '''

    def check_agreement_subject_pred(self, error_token):
        # Agreement errors:
        #       develop - develops; is (developing) - are (developing); has developed - have developed (Agreement)
        #       is (developing) - were (developing); was (developing) - have been (developing) (Agreement + Choice of Tense)
        # No Agreement error:
        #       is (developing) - was (developing) (Choice os tense)

        error_morph = error_token['token_morph']
        error_number = error_morph.get('Number')
        # morph of plural verbs has no 'Number' parameter
        if not error_number:
            error_number = ['Plur']

        _, correction = self.match_correction(error_token, 3)
        if correction:
            correction_morph = correction['token_morph']
            correction_number = correction_morph.get('Number')

            # morph of plural verbs has no 'Number' parameter
            if not correction_number:
                correction_number = ['Plur']

            if error_number != correction_number:
                # "can agrees" - "can agree" is a case of Tense form error rather than Agreement
                if len(error_token['children_list']):
                    for c in error_token['children_list']:
                        if c[1] in self.construction_dict.keys() and c[1] > self.current_token_id - 3:
                            child = self.construction_dict[c[1]]
                            if self.is_modal(child) and self.token_in_correction(mode=2, missing=False):
                                self.error_span, self.correction_span = self.span.verb_span(error_token)
                                return 10  # Tense form
                self.correction_span = correction['token']
                return 32  # Agreement

    def check_gerund_participle_pattern(self, error_token):
        infinitive_in_corr = 0

        corr_token_id, correction_token = self.match_correction(error_token, 3)
        if correction_token:
            # "tending" - "tendency"
            if correction_token['token_pos'] == 'NOUN':
                self.correction_span = correction_token['token']
                return 44  # Confusion of category

            if self.check_voice(correction_token):
                self.error_span, self.correction_span = self.span.verb_span(error_token)
                return 11  # Voice

            if self.check_verb_pattern(error=[self.current_token_id, error_token],
                                       correction=[corr_token_id, correction_token]):
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                return 13  # Verb pattern

            if self.is_finite_verb(error_token) and self.is_perfect(correction_token):
                # "is demonstrates" - "is demonstrated" (usual auxiliary verb + participle; Tense form)
                # "feel encourage" - "feel encouraged" (lexical verb + participle; Participle construction)
                tag = self.check_tense_form_perfect(error_token, correction_token)
                if tag:
                    return tag

            gerund_error = self.is_gerund(error_token)
            gerund_corr = self.is_gerund(correction_token)
            if gerund_error or gerund_corr:
                # We have to search for auxiliary verbs in error and correction spans.
                # "were use" - "were using" or "making" - "are making" (auxiliary verbs found)
                # are the cases of Tense Form error,
                # while "get - getting" (no auxiliary verbs)
                # are the cases of Gerund or participle construction error
                tag = self.check_tense_form_gerund(error_token, correction_token)
                if tag:
                    return tag

            # "comparing with" - "compared to"
            if gerund_error and self.is_perfect(correction_token) and \
                    error_token['token_lemma'] == correction_token['token_lemma'] == 'compare':
                if corr_token_id + 1 in self.full_correction.keys():
                    preposition = self.full_correction[self.current_token_id + 1]
                    if preposition['token'] == 'to':
                        self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                        return 37  # Comparative construction

            # "achieving" - "to achieve" (Infinitive construction)
            # "decision of applying" - "decision to apply" (Noun+Infinitive)
            error_inf = self.is_infinitive(token=error_token, token_id=self.current_token_id)
            correction_inf = self.is_infinitive(token=correction_token, token_id=corr_token_id, correction=1)
            if error_inf != correction_inf:
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)

                if correction_inf and len(correction_token['ancestor_list']):
                    for a in correction_token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] in ['NOUN', 'PROPN']:
                            return 20  # Noun + Infinitive

                # "borrow" - "to borrow"
                error_finite = self.is_finite_verb(error_token)
                correction_finite = self.is_finite_verb(correction_token)

                if not error_inf and error_finite and len(error_token['children_list']):
                    for c in error_token['children_list']:
                        if c[1] in self.construction_dict.keys():
                            child = self.construction_dict[c[1]]
                            if child['token_pos'] == 'VERB' and not self.is_modal(child) and \
                                    self.is_infinitive(token=child,
                                                       token_id=c[1],
                                                       correction=0):
                                return 35  # Parallel construction

                if not correction_inf and correction_finite and len(correction_token['children_list']):
                    for cc in correction_token['children_list']:
                        child = self.full_correction[cc[1]]
                        if child['token_pos'] == 'VERB' and not self.is_modal(child) and \
                                self.is_infinitive(token=child,
                                                   token_id=cc[1],
                                                   correction=1):
                            infinitive_in_corr = 1
                            # "prefer to walk, to talk and to play" - "prefer to walk, talk and play"
                            if len(child['children_list']):
                                for token in child['children_list']:
                                    if token['token'] in self.coordinating_conj or token['token'] == ',':
                                        return 35  # Parallel construction
                            break
                    # "lets them walk, to talk and to play" - "lets them walk, talk and play"
                    if not infinitive_in_corr:
                        return 35  # Parallel construction

                return 15  # Infinitive construction

    def check_tense_simple(self, error_token):
        corr_tense, corr_aspect, corr_mood = [], [], []
        error_aux, corr_aux = False, False
        corr_id, correction = None, None
        tag = None

        error_aux = True if error_token['token_pos'] == 'AUX' else False
        morph = error_token['token_morph']
        tense = morph.get('Tense')
        mood = morph.get('Mood')
        # infinitive verbs do not have Tense property
        if not tense and self.is_finite_verb(error_token):
            tense = ['Pres']

        # there are many possibilities of how correction might differ from the error,
        #
        # for example, "have chosen" - "chose" (2 tokens in the error (analytical predicate), 1 token in the correction)
        # "chose" - "have chosen" (1 token in the error - 2 tokens in the correction)
        # (had) "been breaking" - (had) "broken" (part of auxiliary construction in the error span and participle in the correction),
        #
        # so we firstly look for auxiliary verb and take grammatical information from it
        for corr_id, correction in self.correction.items():
            if correction['token_pos'] == 'AUX':
                corr_morph = correction['token_morph']
                corr_tense = corr_morph.get('Tense')
                corr_mood = corr_morph.get('Mood')
                corr_aux = True
                break

        # auxiliary verbs in different tenses in the error and the correction
        # "was playing" - "is playing" (Past - Pres)
        # "was playing" - "has played" (Past - Pres)
        #
        # lexical verb in the error, auxiliary verb in the correction; verbs are in different tenses
        # "plays" - "was playing" (Pres - Past)
        if not tag and tense and corr_tense and tense[0] != corr_tense[0]:
            tag = 9  # Choice of tense

        # "start" - "have started" - both the verb in the error and the auxiliary verb are in present tense,
        # so if we only examine the auxiliary verb, we will not detect the error
        # in this case we have to look at the tense of participle
        #
        # moreover, if auxiliary verb is not found in the correction,
        # we also have to look at the participle
        if not tag:
            for corr_id, correction in self.correction.items():
                if correction['token_pos'] == 'VERB':
                    corr_morph = correction['token_morph']
                    corr_tense = corr_morph.get('Tense')
                    # infinitive verbs do not have Tense property
                    if not corr_tense and self.is_finite_verb(correction):
                        corr_tense = ['Pres']
                    break

        # auxiliary verb in the error, lexical verb in the correction; verbs are in different tenses
        # "is playing" - "played" (Pres - Past)
        #
        # lexical verbs in different tenses in the error and the correction
        # "plays" - "played" (Pres - Past)
        if not tag and tense and corr_tense and tense[0] != corr_tense[0]:
            tag = 9  # Choice of tense

        # further examination
        if not tag:
            # "was" vs "had": both refer to the past tense, but have different 'Mood' properties
            # "had developed" - "was developing" (no 'Mood' property - 'Mood=Ind')
            if error_aux and corr_aux:
                if len(mood) != len(corr_mood):
                    tag = 9  # Choice of tense

            # error contains auxiliary "will" referring to the future, while correction does not - and vice versa
            # "will play" - "plays" (Future - Pres)
            # "was playing" - "will be playing" (Past - Future)
            #
            # if both error and correction contain "will", we have to check progressive participles
            error_future = error_aux and error_token['token_lemma'] == 'will'
            corr_future = corr_aux and correction['token_lemma'] == 'will' if corr_id else False
            if not tag and error_future != corr_future:
                # "will accept" - "would accept" / "could accept" / "might accept" etc.
                tag = self.check_modals(error_token)
                if not tag:
                    tag = 9  # Choice of tense

        return tag, corr_id

    def check_verb(self, error_token, only_check_tense=0):
        error, correction = {}, {}
        voice_error_found = 0

        # firstly, we check gerund/participle/infinitive errors and voice error rather than checking choice of tense
        # however, Choice of tense error and Voice error can be applied to the same construction
        # f.e., "concentrates on" - "was concentrated on"
        # which means that if we detect Voice error, we have to specifically check Choice of tense error later
        if not only_check_tense:
            tag = self.check_gerund_participle_pattern(error_token)
            if tag:
                return tag

        tag, corr_id = self.check_tense_simple(error_token)
        if tag:
            if tag != 12:
                self.error_span, self.correction_span = self.span.verb_span(error_token)
            return tag

        # finite form in the error span and continuous form in the correction and vice versa
        #
        # "plays" - "is playing"
        # "was playing" - "played"
        # "has played" - "has been playing"
        if error_token['token_pos'] == 'VERB':
            error = error_token
            _, correction = self.match_correction(error_token, 1)
        elif error_token['token_pos'] == 'AUX' and len(error_token['ancestor_list']):
            for a in error_token['ancestor_list']:
                ancestor = self.construction_dict[a[1]]
                if ancestor['token_pos'] == 'VERB':
                    error = ancestor
                    _, correction = self.match_correction(ancestor, 1)
                    break

        if len(error.keys()) and len(correction.keys()) and \
                self.check_continuous(error, correction):
            self.error_span, self.correction_span = self.span.verb_span(error_token)
            # "are really enjoying" - "really enjoy" / "were playing" - "played"
            # when we broaden the error span, we also place a redundant auxiliary verb in the correction
            # ("are really enjoying" - "are really enjoy"), so in that case we have to forcibly narrow the correction span
            if self.is_gerund(error) and self.is_finite_verb(correction):
                self.correction_span = ' '.join(self.correction_span.split()[1:])
            return 9  # Choice of tense

        if voice_error_found:
            self.error_span, self.correction_span = self.span.verb_span(error_token)
            return 11  # Voice

    def check_irregular(self, error_token):
        # "does not haves" - "does not have"
        if error_token['token'] == 'haves':
            for correction in self.correction.values():
                if correction['token'].lower() == 'have':
                    return 10  # Tense form

        # "rised" - "rose"
        # "sleeped" - "slept"
        for correction in self.correction.values():
            if error_token['token_lemma'] == correction['token_lemma'] and \
                    correction['token_lemma'] in irregular_verbs.keys() and \
                    correction['token'].lower() in irregular_verbs[correction['token_lemma']]:
                return 10  # Tense form

    def check_tense_form_gerund(self, error_token, correction_token):
        aux_in_error_id, aux_in_corr_id = 0, 0
        aux_in_error, aux_in_corr = {}, {}

        gerund_error = self.is_gerund(error_token)
        gerund_corr = self.is_gerund(correction_token)

        finite_error = self.is_finite_verb(error_token)
        finite_corr = self.is_finite_verb(correction_token)

        if len(error_token['ancestor_list']):
            for a in error_token['ancestor_list']:
                if a[1] in self.construction_dict.keys():
                    ancestor = self.construction_dict[a[1]]
                    if ancestor['token_pos'] == 'AUX':
                        aux_in_error_id = a[1]
                        aux_in_error[a[1]] = ancestor
                        break
        if not len(aux_in_error.keys()) and len(error_token['children_list']):
            for c in error_token['children_list']:
                if c[1] in self.construction_dict.keys():
                    child = self.construction_dict[c[1]]
                    if child['token_pos'] == 'AUX':
                        aux_in_error_id = c[1]
                        aux_in_error[c[1]] = child
                        break

        if len(correction_token['ancestor_list']):
            for aa in correction_token['ancestor_list']:
                ancestor = self.full_correction[aa[1]]
                if ancestor['token_pos'] == 'AUX':
                    aux_in_corr_id = aa[1]
                    aux_in_corr[aa[1]] = ancestor
                    break
        if not len(aux_in_corr.keys()) and len(correction_token['children_list']):
            for cc in correction_token['children_list']:
                child = self.full_correction[cc[1]]
                if child['token_pos'] == 'AUX':
                    aux_in_corr_id = cc[1]
                    aux_in_corr[cc[1]] = child
                    break

        # "we making" - "we are making"
        if gerund_error and gerund_corr and len(aux_in_error.keys()) != len(aux_in_corr.keys()):
            self.error_span, self.correction_span = self.span.verb_span(error_token)
            return 10  # Tense Form

        # "do not feeling" - "do not feel"
        # "will providing" - "will provide"
        # "we making" - "we make"
        # "are make" - "are making"
        if (gerund_error and finite_corr) or (finite_error and gerund_corr):
            if len(aux_in_error.keys()) and len(aux_in_corr.keys()) and \
                    aux_in_error[aux_in_error_id]['token_lemma'] == aux_in_corr[aux_in_corr_id]['token_lemma'] and \
                    aux_in_error[aux_in_error_id]['token_lemma'] in ['be', 'do', 'will']:
                self.error_span, self.correction_span = self.span.verb_span(error_token)
                return 10  # Tense Form

            # "people watching TV every day" - "people watch TV every day" (Tense form)
            # "they are not interested in do something" - "they are not interested in doing something" (Gerund or participle construction)
            elif not len(aux_in_error.keys()) and not len(aux_in_corr.keys()):
                if gerund_error and finite_corr:
                    self.error_span, self.correction_span = self.span.verb_span(error_token)
                    return 10  # Tense Form
                elif finite_error and gerund_corr:
                    self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                    return 14  # Gerund or participle construction

    def check_tense_form_perfect(self, error_token, correction_token):
        auxiliary_verbs = ['be', 'do', 'have', 'will']
        aux_in_error_id, aux_in_corr_id = 0, 0
        aux_in_error, aux_in_corr = {}, {}

        if len(error_token['ancestor_list']):
            for a in error_token['ancestor_list']:
                if a[1] in self.construction_dict.keys():
                    ancestor = self.construction_dict[a[1]]
                    if ancestor['token_pos'] == 'AUX' and ancestor['token_lemma'] in auxiliary_verbs:
                        aux_in_error_id = a[1]
                        aux_in_error[a[1]] = ancestor
                        break
        elif not len(aux_in_error.keys()) and len(error_token['children_list']):
            for c in error_token['children_list']:
                if c[1] in self.construction_dict.keys():
                    child = self.construction_dict[c[1]]
                    if child['token_pos'] == 'AUX' and child['token_lemma'] in auxiliary_verbs:
                        aux_in_error_id = c[1]
                        aux_in_error[c[1]] = child
                        break

        if len(correction_token['ancestor_list']):
            for aa in correction_token['ancestor_list']:
                ancestor = self.full_correction[aa[1]]
                if ancestor['token_pos'] == 'AUX' and ancestor['token_lemma'] in auxiliary_verbs:
                    aux_in_corr_id = aa[1]
                    aux_in_corr[aa[1]] = ancestor
                    break
        elif not len(aux_in_corr.keys()) and len(correction_token['children_list']):
            for cc in correction_token['children_list']:
                child = self.full_correction[cc[1]]
                if child['token_pos'] == 'AUX' and child['token_lemma'] in auxiliary_verbs:
                    aux_in_corr_id = cc[1]
                    aux_in_corr[cc[1]] = child
                    break

        # "are respect" — "are respected"
        # "should be produces" - "should be produced"
        # "was reaches" - "was reached"
        # "have been praise" — "have been praised"
        if len(aux_in_error.keys()) and len(aux_in_corr.keys()) and \
                aux_in_error[aux_in_error_id]['token_lemma'] == aux_in_corr[aux_in_corr_id]['token_lemma']:
            if self.is_modal(aux_in_error[aux_in_error_id]) and self.is_modal(aux_in_corr[aux_in_corr_id]):
                self.error_span, self.correction_span = self.span.verb_span(error_token)
                return 10  # Tense Form

            aux_error_tense = aux_in_error[aux_in_error_id]['token_morph'].get('Tense')
            aux_corr_tense = aux_in_corr[aux_in_corr_id]['token_morph'].get('Tense')
            if aux_error_tense and aux_corr_tense and aux_error_tense[0] == aux_corr_tense[0]:
                self.error_span, self.correction_span = self.span.verb_span(error_token)
                return 10  # Tense Form

        # "feel encourage" - "feel encouraged" (lexical verb + participle)
        elif len(aux_in_error.keys()) and len(aux_in_corr.keys()):
            self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
            return 14  # Gerund or participle construction

    def check_pattern(self, error_token):
        error_prep, corr_prep = '', ''

        # cases like "carried" - "carried out"
        # other types of Verb Patter error like "avoid visit" - "avoid visiting" are examined in other rules

        _, correction_match = self.match_correction(error_token, 0)
        if correction_match:
            if len(correction_match['children_list']):
                for cc in correction_match['children_list']:
                    child = self.full_correction[cc[1]]
                    if child['token_tag'] in self.prepositions:
                        corr_prep = child['token'].lower()
                        break

            if len(error_token['children_list']):
                for c in error_token['children_list']:
                    child = self.construction_dict[c[1]]
                    if child['token_tag'] in self.prepositions:
                        error_prep = child['token']
                        break

            if error_prep != corr_prep:
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                return 13  # Verb pattern

        # if we have not detected a Verb pattern error, we have to check for prepositional errors,
        # because we have previously excluded prepositional rule from the list of rules
        return self.check_prepositions(error_token)

    '''
    Others
    '''

    def check_comparison(self, error_token):
        degrees = ['more', 'less', 'most', 'least']

        # deep - deeper
        comparative_error = self.is_comparative(error_token)
        comparative_correction = self.token_in_correction(mode=7, missing=False)
        if comparative_error != comparative_correction:
            self.error_span, self.correction_span = self.span.comparative_construction_span(error_token, tag=29)
            return 29  # Degree of comparison

        _, correction = self.match_correction(error_token, mode=7)
        if len(correction.keys()):
            # independenter - more independent / more slow - slower
            if (error_token['token'] in degrees and
                correction['token'].lower() not in degrees and correction['token'].lower() not in self.quantifiers) or \
                    (error_token['token'] not in degrees and error_token['token'] not in self.quantifiers and
                     correction['token'].lower() in degrees):
                self.error_span, self.correction_span = self.span.comparative_construction_span(error_token, tag=29)
                return 29

            # more comfortable - the most comfortable
            # less comfortable - the least comfortable
            degree_error = error_token['token_morph'].get('Degree')
            degree_correction = correction['token_morph'].get('Degree')
            if error_token['token_pos'] != correction['token_pos'] or \
                    degree_error[0] != degree_correction[0]:
                self.error_span, self.correction_span = self.span.comparative_construction_span(error_token, tag=29)
                return 29

    def check_comparative_construction(self):
        returned_num_error, returned_num_corr = 0, 0

        comparative_error = self.find_comparative_construction(correction=False)
        comparative_corr = self.find_comparative_construction(correction=True)

        if comparative_error[0] != comparative_corr[0]:
            self.error_span, self.correction_span = self.span.comparative_construction_span(error_token='', tag=37)
            return 37  # Comparative construction

        if len(comparative_error) > 1:
            returned_num_error = comparative_error[1]
        if len(comparative_corr) > 1:
            returned_num_corr = comparative_corr[1]
        # "as modern" - "as modern as"
        # "more than that" - "less than that"
        if returned_num_error != returned_num_corr:
            self.error_span, self.correction_span = self.span.comparative_construction_span(error_token='', tag=37)
            return 37  # Comparative construction

    def check_noun_number(self, error_token, correction_token):
        error_number = error_token['token_morph'].get('Number')
        corr_number = correction_token['token_morph'].get('Number')

        if error_number and corr_number and error_number[0] != corr_number[0]:
            self.correction_span = correction_token['token']

            # "fourth", "fifth", "tenth", "twentieth" etc. are identified as nouns
            # creating a list of all these possible numerals is expensive,
            # so we try to detect them by examining the ending of the lemma
            #
            # we also have to make sure that nouns ending with -th like "strength", "wealth"
            # are not considered numerals

            if self.is_numeral_noun(error_token):
                if error_token['token_lemma'] == 'percent':
                    self.error_span, self.correction_span = self.span.numerals_span(error_token)
                return 30  # Numerals
            # if self.check_collective_noun(error_token):
            #     self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
            #     return 26  # Adjective as a collective noun
            return 21  # Noun number

    def check_noun_gerund(self, error_token, correction_token):
        ending_error, ending_corr = 3, 3

        # "attending of gym" - "attendance of gym"
        error_number = error_token['token_morph'].get('Number')
        corr_number = correction_token['token_morph'].get('Number')
        if error_number and corr_number:
            if error_number[0] == 'Sing':
                ing_error = error_token['token'].endswith('ing')
            else:
                ing_error = error_token['token'].endswith('ings')
                ending_error = 4

            if corr_number[0] == 'Sing':
                ing_corr = correction_token['token'].endswith('ing')
            else:
                ing_corr = correction_token['token'].endswith('ings')
                ending_corr = 4

            # we assume that the length of the base of gerund forms has to be 3 symbols and more ("making", "asking" etc.)
            # so that we do not consider nouns like "ring", "king", "thing" gerunds
            # "being" is the exception
            if ing_error != ing_corr and ((len(error_token['token']) - ending_error >= 3 and
                                           len(correction_token['token']) - ending_corr >= 3)):
                if ing_error:
                    error_root = error_token['token'].lower()[:-ending_error]
                    if correction_token['token'].startswith(error_root):
                        return 44  # Confusion of a category
                elif ing_corr:
                    corr_root = correction_token['token'][:-ending_corr]
                    if error_token['token'].lower().startswith(corr_root):
                        return 44  # Confusion of a category

            elif ing_error != ing_corr and ((error_token['token'].lower() == 'being') and
                                            correction_token['token'].startswith('be') or
                                            (correction_token['token'] == 'being' and
                                             error_token['token'].lower().startswith('be'))):
                return 44  # Confusion of a category

    def check_possessive(self, error_token):
        if "'" in error_token['token']:
            if error_token['token_pos'] not in ['NOUN', 'PROPN']:
                prev_token = self.sentence_tokens[self.current_token_id - 1]
                if prev_token['token_pos'] in ['NOUN', 'PROPN']:
                    for corr_token in self.correction.values():
                        if corr_token['token'] == 's':
                            self.error_span, self.correction_span = self.span.possessive_span(error_token)
                            return 19  # Possessive form of noun
            else:
                for corr_token in self.full_correction.values():
                    if corr_token['token'] == "'s":
                        self.error_span = [self.full_error['error'], self.full_error['idx_1'], self.full_error['idx_2']]
                        self.correction_span = self.full_error['correction']
                        return 19  # Possessive form of noun

        elif error_token['token_pos'] in ['NOUN', 'PROPN'] and self.token_in_error(mode=12, missing=True):
            for corr_id, corr_token in self.full_correction.items():
                if "'" in corr_token['token']:
                    if corr_id - 1 in self.full_correction.keys():
                        prev_token = self.full_correction[corr_id - 1]
                        if prev_token['token_pos'] in ['NOUN', 'PROPN']:
                            self.correction_span = prev_token['token'] + corr_token['token']
                    else:
                        self.correction_span = corr_token['token']
                    return 19  # Possessive form of noun

    def check_numerals(self, error_token):
        if error_token['token_tag'] in pos_dict['NUM']:
            self.error_span, self.correction_span = self.span.numerals_span(error_token)
            return 30  # Numerals
        _, correction = self.match_correction(error_token, 6)
        if len(correction.keys()) != 0:
            ending_error = re.findall(r'\D+', error_token['token'])
            ending_corr = re.findall(r'\D+', correction['token'])
            if ((len(ending_error) and not len(ending_corr)) or (not len(ending_error) and len(ending_corr)) or
                    ending_error[-1] != ending_corr[-1]):
                return 30  # Numerals

    """
    Vocabulary rules
    """

    def check_compound(self, error_token):
        if "-" in error_token['token']:
            for corr_token in self.correction.values():
                # "alcohol-contain" - "alcohol-containing"
                if "-" in corr_token['token'] and corr_token['token'].lower() != error_token['token']:
                    self.correction_span = corr_token['token']
                    return 45
        else:
            for corr_token in self.correction.values():
                # "fifteen years period" - "fifteen-year period"
                if "-" in corr_token['token']:
                    self.correction_span = corr_token['token']
                    self.error_span = self.span.compound_word_span(error_token)
                    return 45

    def check_verb_choice(self, error_token):
        for corr_token in self.correction.values():
            if corr_token['token_pos'] == 'VERB' and error_token['token_lemma'] != corr_token['token_lemma']:
                self.correction_span = corr_token['token']
                return 40  # Choice of a lexical item

    def check_lexical_choice(self, error_token, token_id, check_number=True, correct_number=True):
        if error_token['token'] in self.articles:
            return None

        # наивный подход: берём номер текущего токена, ищем соответствующий в области исправления
        if len(self.correction.keys()) >= token_id + 1:
            key = list(self.correction.keys())[token_id]
            correction = self.correction[key]
            if correction['token'].lower() in self.articles or correction['token_pos'] != error_token['token_pos']:
                _, correction = self.match_correction(error_token, mode=1)
        else:
            _, correction = self.match_correction(error_token, mode=1)

        if len(correction.keys()):
            if error_token['token_lemma'] != correction['token_lemma']:
                if check_number:
                    error_number = error_token['token_morph'].get('Number')
                    corr_number = correction['token_morph'].get('Number')

                    if error_number and corr_number:
                        if correct_number and error_number[0] == corr_number[0]:
                            self.correction_span = correction['token']
                            return 40  # Choice of a lexical item

                        elif not correct_number and error_number[0] != corr_number[0]:
                            self.correction_span = correction['token']
                            return 40  # Choice of a lexical item
                    else:
                        self.correction_span = correction['token']
                        return 40  # Choice of a lexical item
                else:
                    self.correction_span = correction['token']
                    return 40  # Choice of a lexical item
        else:
            self.error_span = [error_token['token'], error_token['idx_1'], error_token['idx_2']]
            self.correction_span = ' '
            return 51  # Redundant component in clause or sentence
