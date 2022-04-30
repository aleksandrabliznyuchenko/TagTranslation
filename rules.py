import re

from dictionaries import irregular_verbs, uncountable_nouns, pos_dict
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
            corr_id, correction_match = self.match_correction(error_token, 2)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                self.error_span, self.correction_span = self.span.articles_span(
                    [self.current_token_id, error_token],
                    [corr_id, correction_match]
                )
                return 5  # Articles
            else:
                article_id, article = self.span.token_in_correction(mode=3)
                if not len(article.keys()):
                    self.error_span, self.correction_span = self.span.articles_span(
                        [self.current_token_id, error_token], []
                    )
                    # "few" - "a few" / "a fewer" - "fewer"
                    if len(error_token['ancestor_list']):
                        for a in error_token['ancestor_list']:
                            if a[1] in self.construction_dict.keys():
                                ancestor = self.construction_dict[a[1]]
                                if ancestor['token'] in self.quantifiers:
                                    return 6  # Quantifiers
                    return 5  # Articles
        else:
            article_id, article = self.span.token_in_correction(mode=3)
            if len(article.keys()):
                # "more independent" - "the most independent" -- this case will be annotated later on
                if len(article['ancestor_list']):
                    for a in article['ancestor_list']:
                        if a[1] in self.construction_dict.keys():
                            ancestor = self.construction_dict[a[1]]
                            if ancestor['token_pos'] in ['ADJ', 'ADV'] and len(ancestor['children_list']):
                                for c in ancestor['children_list']:
                                    if c[0] == 'most':
                                        return None

                # "few" - "a few" / "a fewer" - "fewer"
                if len(article['ancestor_list']):
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
                # "there is a sign" - "it is a sign" is a case of Confusion of structures error
                if (error_token['token'] == 'there' and correction_match['token'].lower() == 'it') or \
                        (error_token['token'] == 'it' and correction_match['token'].lower() == 'there'):
                    return 38  # Confusion of structures
                return 31  # Pronouns
            elif correction_match and self.token_in_correction(mode=5, missing=True):
                return 31
        else:
            pron_id, pronoun = self.span.token_in_correction(mode=5, missing=False)
            if len(pronoun.keys()) and len(pronoun['ancestor_list']):
                for a in pronoun['ancestor_list']:
                    ancestor = self.full_correction[a[1]]
                    if self.is_finite_verb(ancestor):
                        verb_id, verb = self.span.match_error_token(ancestor, a[1], mode=2)
                        if len(verb.keys()) and len(verb['ancestor_list']):
                            for aa in verb['ancestor_list']:
                                verb_ancestor = self.sentence_tokens[aa[1]]
                                if self.is_finite_verb(verb_ancestor) and aa[1] != verb_id and \
                                        len(verb_ancestor['children_list']):
                                    for c in verb_ancestor['children_list']:
                                        child = self.sentence_tokens[c[1]]
                                        if child['token_pos'] == 'PRON':
                                            return 35  # Parallel construction

            return 31

    def check_determiners(self, error_token):
        if error_token['token_tag'] == 'DT' and not error_token['token'] in self.articles:
            _, correction_match = self.match_correction(error_token, 9)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                # "this glasses" - "these glasses" is a case of Agreement error
                error_number = error_token['token_morph'].get('Number')
                corr_number = correction_match['token_morph'].get('Number')
                if error_number and corr_number and error_number != corr_number and \
                        self.construction_dict[error_token['token_head']] in self.construction_dict.keys():
                    error_head_number = self.construction_dict[error_token['token_head']]['token_morph'].get('Number')
                    if error_head_number and error_head_number != corr_number:
                        return 32  # Agreement
                return 4  # Determiners
            elif correction_match and self.token_in_correction(mode=9, missing=True):
                return 4  # Determiners
        elif self.token_in_correction(mode=9, missing=False):
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
                return 6  # Quantifiers
            elif correction_match and self.token_in_correction(mode=10, missing=True):
                return 6  # Quantifiers
        elif self.token_in_correction(mode=10, missing=False):
            return 6  # Quantifiers

    def check_modals(self, error_token):
        # "can allow" - "might allow"
        # "I rather agree" - "I would rather agree"

        if self.is_modal(error_token):
            _, correction_match = self.match_correction(error_token, 4)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                self.error_span, self.correction_span = self.span.modals_span(error_token)
                return 12  # Modals
            elif correction_match and self.token_in_correction(mode=2, missing=True):
                self.error_span, self.correction_span = self.span.modals_span(error_token)
                return 12
        elif self.token_in_correction(mode=2, missing=False):
            self.error_span, self.correction_span = self.span.modals_span(error_token, modal_error=0)
            return 12

    def check_prepositions(self, error_token):
        # TODO: Prepositional adverb, "almost" - "around" (make a list of such adverbs?)

        # if the preposition is determined by the noun, the tag Prepositional noun is chosen;
        # if the preposition is determined by the adjective, the tag Prepositional adjective is chosen;
        # if the preposition is determined by the adverb, the tag Prepositional adverb is chosen;
        # in other cases the preposition is independent and tag Prepositions is chosen
        #
        # "increase of" - "increase in" (Prepositional noun)
        # "regardless the loss" - "regardless of the loss" (Prepositional adjective)
        # "except" - "except for" (Prepositional adverb)
        # "the growth increased for this period" - "the growth increased during this period" (Prepositions)

        if error_token['token_tag'] in self.prepositions or error_token['token_pos'] in self.prepositions:
            preposition_head = self.construction_dict[error_token['token_head']]
            # "more than", "less than" -- this case will be examined later
            if preposition_head['token'] in ['more', 'less'] and error_token['token'] == 'than':
                return None
            if preposition_head['token_pos'] == 'NOUN':
                tag = 18  # Prepositional noun
            elif preposition_head['token_pos'] == 'ADJ':
                tag = 25  # Prepositional adjective
            elif error_token['token_pos'] == 'ADV':
                return 28  # Prepositional adverb
            else:
                tag = 22  # Prepositions

            corr_id, correction_match = self.match_correction(error_token, 1)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                if tag != 22:
                    self.error_span, self.correction_span = self.span.prepositions_span(
                        [self.current_token_id, error_token],
                        [corr_id, correction_match], tag
                    )
                return tag
            else:
                prep_id, preposition = self.span.token_in_correction(mode=1)
                if not len(preposition.keys()) and tag != 22:
                    self.error_span, self.correction_span = self.span.prepositions_span(
                        [self.current_token_id, error_token], [], tag
                    )
                return tag
        else:
            prep_id, preposition = self.span.token_in_correction(mode=1)
            if len(preposition.keys()):
                preposition_head = self.full_correction[preposition['token_head']]
                # "the most women" - "most of women" -- this case will be examined later
                if preposition_head['token'] == 'most':
                    return None
                # "more than", "less than" -- this case will be examined later
                if preposition_head['token'] in ['more', 'less'] and preposition['token'] == 'than':
                    return None
                if preposition_head['token_pos'] == 'NOUN':
                    self.error_span, self.correction_span = self.span.prepositions_span(
                        [], [prep_id, preposition], 18
                    )
                    return 18  # Prepositional noun
                if preposition_head['token_pos'] == 'ADJ':
                    self.error_span, self.correction_span = self.span.prepositions_span(
                        [], [prep_id, preposition], 25
                    )
                    return 25  # Prepositional adjective
                elif preposition_head['token_pos'] == 'ADV':
                    self.error_span, self.correction_span = self.span.prepositions_span(
                        [], [prep_id, preposition], 28
                    )
                    return 28  # Prepositional adverb
                # "for borrowing or buying" - "for borrowing or for buying"
                # (the head of the added preposition is the first preposition)
                elif preposition_head['token'] == preposition['token'] and preposition['token_head'] != prep_id:
                    if self.is_gerund(error_token) and len(error_token['ancestor_list']):
                        for a in error_token['ancestor_list']:
                            ancestor = self.sentence_tokens[a[1]]
                            if ancestor['token'] == preposition['token'] and a[1] < self.current_token_id and \
                                    len(ancestor['children_list']):
                                for c in ancestor['children_list']:
                                    child = self.sentence_tokens[c[1]]
                                    if self.is_gerund(child):
                                        self.correction_span = preposition['token'] + ' ' + error_token['token']
                                        return 36  # Parallel constructions
                else:
                    return 22  # Prepositions

    def check_conjunctions(self, error_token):
        # "That stands out is that..." - "What stands out is that..."
        # "women between 55 to 65" - "women between 55 and 65"
        # "it is up to everybody to decide whether which side should they take" - "it is up to everybody to decide which side should they take"
        if self.is_conjunction(error_token):
            _, correction_match = self.match_correction(error_token, 5)
            if correction_match and correction_match['token'].lower() != error_token['token']:
                if correction_match['token'].lower() in self.relative_conj:
                    return 34  # Relative clauses
                return 23  # Conjunctions
            elif correction_match and self.token_in_correction(mode=4, missing=True):
                return 23
        else:
            _, corr_token = self.span.token_in_correction(mode=4, missing=False)
            if corr_token:
                if corr_token['token'].lower() in self.relative_conj:
                    return 34  # Relative clauses
                return 23

    def check_negation(self, error_token):
        if self.is_negative(error_token):
            corr_id, correction_match = self.match_correction(error_token, mode=13)
            if not correction_match:
                corr_id, correction_match = self.match_correction(error_token, mode=1)
            if correction_match:
                if correction_match['token'].lower() != error_token['token']:
                    return 36  # Negation
                # "need not" - "do not need"
                elif error_token['token'] == 'not' and \
                        self.current_token_id - 1 in self.sentence_tokens.keys() and \
                        corr_id - 1 in self.full_correction.keys():
                    prev_token_error = self.sentence_tokens[self.current_token_id - 1]
                    prev_token_corr = self.full_correction[corr_id - 1]
                    if prev_token_error['token_lemma'] != 'do' and prev_token_corr['token_lemma'] == 'do':
                        return 36  # Negation
            elif correction_match and self.token_in_correction(mode=13, missing=True):
                return 36  # Negation
        elif self.token_in_correction(mode=13, missing=False):
            return 36  # Negation

    '''
    Verbal rules
    '''

    def check_agreement_subject_pred(self, error_token):
        correction_number = []

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

        # is developing - develop; develop - have developed (Agreement + Choice of Tense)
        # look at her - is staring at her (Agreement + Choice of Tense + Choice of lexical item)
        else:
            if error_token['token_pos'] == 'VERB':
                for correction in self.full_correction.values():
                    if correction['token_pos'] == 'AUX':
                        correction_morph = correction['token_morph']
                        correction_number = correction_morph.get('Number')
                        break
            elif error_token['token_pos'] == 'AUX':
                for correction in self.full_correction.values():
                    if correction['token_pos'] == 'VERB' and not self.is_participle(correction):
                        correction_morph = correction['token_morph']
                        correction_number = correction_morph.get('Number')
                        break

        # morph of plural verbs has no 'Number' parameter
        if not correction_number:
            correction_number = ['Plur']

        if error_number != correction_number:
            self.error_span, self.correction_span = self.span.verb_span(error_token)
            return 32  # Agreement

    def check_gerund_participle_pattern(self, error_token):
        infinitive_in_corr = 0

        corr_token_id, correction_token = self.match_correction(error_token, 3)
        if correction_token:
            # "tending" - "tendency"
            if correction_token['token_pos'] == 'NOUN':
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                return 44  # Confusion of category

            if self.check_voice(correction_token):
                self.error_span, self.correction_span = self.span.verb_span(error_token)
                return 11  # Voice

            if self.check_verb_pattern(error_token, correction_token):
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                return 13  # Verb pattern

            # "feel encourage" - "feel encouraged"
            if self.is_finite_verb(error_token) and self.is_participle(correction_token):
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                return 14  # Gerund or participle construction

            # "get" - "getting"
            if not self.is_gerund(error_token) and self.is_gerund(correction_token):
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                return 14  # Gerund or participle construction

            # "comparing with" - "compared to"
            if self.is_gerund(error_token) and self.is_perfect(correction_token) and \
                    error_token['token_lemma'] == correction_token['token_lemma'] == 'compare':
                if corr_token_id + 1 in self.full_correction.keys():
                    preposition = self.full_correction[self.current_token_id + 1]
                    if preposition['token'] == 'to':
                        self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)
                        return 37  # Comparative construction

            # "achieving" - "to achieve" (Infinitive construction)
            # "decision of applying" - "decision to apply" (Noun+Infinitive)
            error_inf = self.is_infinitive(error_token)
            correction_inf = self.is_infinitive(correction_token)
            if error_inf != correction_inf:
                self.error_span, self.correction_span = self.span.gerund_part_inf_span(error_token)

                if correction_inf and len(correction_token['ancestor_list']):
                    for a in correction_token['ancestor_list']:
                        ancestor = self.full_correction[a[1]]
                        if ancestor['token_pos'] == 'NOUN':
                            return 20  # Noun + Infinitive

                # "borrow" - "to borrow"
                error_finite = self.is_finite_verb(error_token)
                correction_finite = self.is_finite_verb(correction_token)

                if not error_inf and error_finite and len(error_token['children_list']):
                    for c in error_token['children_list']:
                        if c[1] in self.construction_dict.keys():
                            child = self.construction_dict[c[1]]
                            if child['token_pos'] == 'VERB' and self.is_infinitive(child):
                                return 35  # Parallel construction

                if not correction_inf and correction_finite and len(correction_token['children_list']):
                    for cc in correction_token['children_list']:
                        child = self.full_correction[cc[1]]
                        if child['token_pos'] == 'VERB' and self.is_infinitive(child):
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

        # there are many possibilities of how correction might differ from the error,
        #
        # for example, "have chosen" - "chose" (2 tokens in the error (analytical predicate), 1 token in the correction)
        # "chose" - "have chosen" (1 token in the error - 2 tokens in the correction)
        # (had) "been broken" - (had) "broken" (part of auxiliary construction in the error span and participle in the correction),
        #
        # so we firstly look for auxiliary verb and take grammatical information from it
        # for corr_id, correction in self.full_correction.items():
        for corr_id, correction in self.correction.items():
            if correction['token_pos'] == 'AUX':
                corr_morph = correction['token_morph']
                corr_tense = corr_morph.get('Tense')
                corr_mood = corr_morph.get('Mood')
                corr_aux = True
                break
        # if auxiliary verb is not found in the correction,
        # we simply look for the ROOT and take grammatical information from it
        if not corr_aux:
            # for corr_id, correction in self.full_correction.items():
            for corr_id, correction in self.correction.items():
                if correction['token_pos'] == 'VERB':
                    corr_morph = correction['token_morph']
                    corr_tense = corr_morph.get('Tense')
                    break

        # auxiliary verbs in different tenses in the error and the correction
        # "was playing" - "is playing" (Past - Pres)
        # "was playing" - "has played" (Past - Pres)
        #
        # auxiliary verb in the error, lexical verb in the correction - and vice versa; verbs are in different tenses
        # "plays" - "was playing" (Pres - Past)
        # "has been playing" - "played" (Pres - Past)
        #
        # lexical verbs in different tenses in the error and the correction
        # "plays" - "played" (Pres - Past)

        if not tag and tense and corr_tense and tense[0] != corr_tense[0]:
            tag = 9  # Choice of tense

        # further examination

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
        if error_future != corr_future:
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
            return 9  # Choice of tense

        if voice_error_found:
            self.error_span, self.correction_span = self.span.verb_span(error_token)
            return 11  # Voice

    def check_tense_form(self):
        # "rised" - "rose"
        # "sleeped" - "slept"

        # TODO: "outweigh" - "outweight"
        # TODO: "can leads" - "can lead"
        # TODO: "starting" - "are starting"; "are share" - "are sharing"
        # TODO: "have lead" - "have led"
        # TODO: "were worked" - "worked" / "were working"; "was reaches" - "reached"; "was focus" - "was focused"
        # TODO: "will not providing" - "will not provide"
        # TODO: "should be produces" - "should be produced"

        for correction in self.correction.values():
            if correction['token_lemma'] in irregular_verbs.keys() and \
                    correction['token'].lower() in irregular_verbs[correction['token_lemma']]:
                return 10  # Tense form

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

    def check_noun_number(self, error_token):
        _, correction = self.match_correction(error_token, 1)
        if len(correction.keys()) != 0:
            error_number = error_token['token_morph'].get('Number')
            corr_number = correction['token_morph'].get('Number')

            if error_number and corr_number and error_number[0] != corr_number[0]:
                self.correction_span = correction['token']

                # "fourth", "fifth", "tenth", "twentienth" etc. are identified as nouns
                # creating a list of all these possible numerals is expensive,
                # so we try to detect them by examining the end of the lemma
                if error_token['token_lemma'] in ['percent', 'hundred', 'thousand', 'million', 'billion'] or \
                        error_token['token_lemma'][:-2] == 'th':
                    return 30  # Numerals
                if error_token['token_lemma'] in uncountable_nouns and \
                        error_token['token_lemma'] == correction['token_lemma']:
                    return 17  # Countable / uncountable nouns
                if self.check_collective_noun(error_token):
                    return 26  # Adjective as a collective noun

                return 21  # Noun number

    def check_noun(self, error_token):
        _, correction = self.match_correction(error_token, 1)
        if len(correction.keys()) != 0:
            possessive, apostrophe = self.check_possessive(error_token, correction)
            if possessive:
                self.error_span, self.correction_span = self.span.possessive_span(error_token, apostrophe)
                return 19  # Possessive form of noun
            if self.check_gerund_noun(error_token, correction):
                return 44  # Confusion of a category

    def check_numerals(self, error_token):
        if error_token['token_tag'] in pos_dict['NUM']:
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

    def check_verb_choice(self, error_token):
        for corr_token in self.correction.values():
            if corr_token['token_pos'] == 'VERB' and error_token['token_lemma'] != corr_token['token_lemma']:
                self.correction_span = corr_token['token']
                return 40  # Choice of a lexical item

    def check_lexical_choice(self, error_token, token_id, check_number=True, correct_number=True):
        # наивный подход: берём номер текущего токена, ищем соответствующий в области исправления
        if len(self.correction.keys()) >= token_id:
            key = list(self.correction.keys())[token_id]
            correction = self.correction[key]
        else:
            _, correction = self.match_correction(error_token, mode=1)

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
