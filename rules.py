from dictionaries import irregular_verbs


class Rules:
    preposition_tags = ["PRF", "PRP", "ADP", "IN"]
    subjects = ["csubj", "csubjpass", "nsubj", "nsubjpass"]
    gerund = ["VBG", "VDG", "VHG", "VVG"]

    def __init__(self):
        self.sentence_dict = {}
        self.error_properties = {}
        self.correction_properties = {}
        self.full_error = {}

    def match_correction(self, error_properties, mode):
        # POS-tag + TreeTagger tag: "number" - "number" / "member"
        if mode == 0:
            for correction in self.correction_properties.values():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_tag'] == error_properties['token_tag']:
                    return correction

        # POS-tag: "number" - "number" / "member" / "amounts"
        elif mode == 1:
            for correction in self.correction_properties.values():
                if correction['token_pos'] == error_properties['token_pos']:
                    return correction

        # POS-tag + TreeTagger tag + lemma: "number" - "number"
        else:
            for correction in self.correction_properties.values():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_tag'] == error_properties['token_tag'] and \
                        correction['token_lemma'] == error_properties['token_lemma']:
                    return correction
        return {}

    """
    Checking word properties (it's part of speech, correct particle form of a verb etc.)
    """

    def predicate_is_analytical(self, token_aux):
        head_id = token_aux['token_head']
        if head_id in self.full_error['tokens'].keys():
            head = self.full_error['tokens'][head_id]
            head_morph = head['token_morph']
            participle = head_morph.get('VerbForm')
            return head['token_dep'] == 'ROOT' and len(participle) != 0 and participle[0] == 'Part'

    def is_modal(self, error):
        return error['token_pos'] == 'AUX' and error['token_tag'] == 'MD'

    def verb_is_passive(self, verb, error=True):
        if error:
            verb_morph = self.sentence_dict[verb.i]['token_morph']
        else:
            verb_morph = self.correction_properties[verb.i]['token_morph']
        aspect = verb_morph.get('Aspect')
        if len(aspect) != 0:
            return aspect[0] == 'Perf'

    def is_preposition(self, token):
        return token['token_tag'] in self.preposition_tags

    def is_participle(self, token):
        verb_form = token['token_morph'].get('VerbForm')
        if verb_form:
            return verb_form[0] == 'Part'

    """
    Checking word form (and whether a form of a word is correct or not)
    """

    def check_irregular_form(self, form):
        irregular = irregular_verbs[self.error_properties['lemma']][form]
        return self.error_properties['token'] != irregular and self.correction_properties['token'] == irregular

    """
    Rules that return tag matches
    """

    def check_articles(self, error):
        error_head = self.sentence_dict[error['token_head']]
        # define correlating token from correction:
        # "a number" - "the number"; "a number" - "the numbers"; "a number" - "the amount"
        correction_head_match = self.match_correction(error_head, 1)
        if correction_head_match:
            correction_head = self.correction_properties[correction_head_match]

            # wrong choice of article: "a number" - "the number"; "a error" - "an error"; "a number" - "the amount"
            for child in correction_head['children_list']:
                if child[1] > correction_head_match:
                    break
                if self.correction_properties[child[1]]['token_dep'] == error['token_dep'] == 'det' and \
                        child[0] != error['token_lemma']:
                    return "Articles"

            # redundant article: "number of the girls" - "number of girls"
            redundant = True
            for child in correction_head['children_list']:
                if child[1] > correction_head_match:
                    break
                if self.correction_properties[child[1]]['token_dep'] == error['token_dep'] == 'det':
                    redundant = False
            if redundant:
                return "Articles"

    def missing_article(self, correction, error):
        # "according to chart" - "according to the chart"
        # TODO: in this case HEPTABOT would set an error span on "to" instead of "chart"
        # we need to develop the error span algorithm first
        return ""

    def check_prepositions_simple(self, error, correction):
        if self.is_preposition(error) and self.is_preposition(correction) and error['token'] != correction['token']:
            return "Prepositions"

    def check_agreement_subject_pred(self, error):
        correction_number = []

        # Agreement errors:
        #       develop - develops; is (developing) - are (developing); has developed - have developed (Agreement)
        #       is (developing) - were (developing); was (developing) - have been (developing) (Agreement + Choice of Tense)
        # No Agreement error:
        #       is (developing) - was (developing) (Choice os tense)

        error_morph = error['token_morph']
        error_number = error_morph.get('Number')
        # morph of plural verbs has no 'Number' parameter
        if len(error_number) == 0:
            error_number = ['Plur']

        correction = self.match_correction(error, 1)
        if correction:
            correction_morph = correction['token_morph']
            correction_number = correction_morph.get('Number')

        # is developing - develop; develop - have developed (Agreement + Choice of Tense)
        # look at her - is staring at her (Agreement + Choice of Tense + Choice of lexical item)
        else:
            if error['token_pos'] == 'VERB':
                for correction in self.correction_properties.values():
                    if correction['token_pos'] == 'AUX':
                        correction_morph = correction['token_morph']
                        correction_number = correction_morph.get('Number')
                        break
            elif error['token_pos'] == 'AUX':
                for correction in self.correction_properties.values():
                    if correction['token_pos'] == 'VERB':
                        correction_morph = correction['token_morph']
                        correction_number = correction_morph.get('Number')
                        break

        # morph of plural verbs has no 'Number' parameter
        if len(correction_number) == 0:
            correction_number = ['Plur']

        if error_number != correction_number:
            return "Agreement"

    def check_agreement_subjects(self):
        # TODO: "_Mineral_ and chemicals are transported by road." --> Subject Agreement instead of Noun Number error
        return ""

    def check_tense(self):
        corr_tense, corr_mood, corr_aspect, aspect = [], [], [], []
        error_aux, corr_aux = False, False
        corr_head_id = None

        error_aux = True if self.error_properties['token_pos'] == 'AUX' else False
        morph = self.error_properties['token_morph']
        tense = morph.get('Tense')
        mood = morph.get('Mood')

        # there are many possibilities of how correction might differ from the error,
        #
        # for example, "have chosen" - "chose" (2 tokens in the error (analytical predicate), 1 token in the correction)
        # "chose" - "have chosen" (1 token in the error - 2 tokens in the correction)
        # (had) "been broken" - (had) "broken" (part of auxiliary construction in the error span and participle in the correction),
        #
        # so we firstly look for auxiliary verb and take grammatical information from it
        for correction in self.correction_properties.values():
            if correction['token_pos'] == 'AUX':
                corr_morph = correction['token_morph']
                corr_tense = corr_morph.get('Tense')
                corr_mood = corr_morph.get('Mood')
                corr_aux = True
                corr_head_id = correction['token_head']
                break
        # if auxiliary verb is not found in the correction,
        # we simply look for the ROOT and take grammatical information from it
        if not corr_aux:
            for correction in self.correction_properties.values():
                if correction['token_dep'] == 'ROOT':
                    corr_morph = correction['token_morph']
                    corr_tense = corr_morph.get('Tense')
                    corr_head_id = correction['token_head']
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
        if len(tense) != 0 and len(corr_tense) != 0 and \
                tense[0] != corr_tense[0]:
            return "Choice of tense"

        # further examination

        # "was" vs "had": both refer to the past tense, but have different 'Mood' properties
        # "had developed" - "was developing" (no 'Mood' property - 'Mood=Ind')
        if error_aux and corr_aux:
            if len(mood) != len(corr_mood):
                return "Choice of tense"

        # error contains auxiliary "will" referring to the future, while correction does not - and vice versa
        # "will play" - "plays" (Future - Pres)
        # "was playing" - "will be playing" (Past - Future)
        #
        # if both error and correction contain "will", we have to check progressive participles
        error_future = error_aux and self.is_modal(self.error_properties) and self.error_properties['lemma'] == 'will'
        corr_future = corr_aux and self.is_modal(correction) and correction['lemma'] == 'will' \
            if corr_head_id else False
        if error_future != corr_future:
            return "Choice of tense"

        # check tenses of participles
        # "have chosen" - "have been choosing" (Past - Pres)
        tense, corr_tense = [], []

        error_head_id = self.error_properties['token_head']
        error_head = self.sentence_dict[error_head_id]
        tense = error_head['token_morph'].get('Tense')
        aspect = error_head['token_morph'].get('Aspect')

        if corr_head_id:
            correction_head = self.correction_properties[corr_head_id]
            corr_tense = correction_head['token_morph'].get('Tense')
            corr_aspect = correction_head['token_morph'].get('Aspect')

        if len(tense) != 0 and len(corr_tense) != 0 and \
                tense[0] != corr_tense[0]:
            return "Choice of tense"

        # check progressive participles
        #
        # "plays" - "is playing": tenses of the lexical verb and auxiliary+participle are the same;
        #                         the difference is in the progressive participle itself:
        #                         one construction contains it, the other does not
        #
        # the same works when both the error and the correction refer to the future
        # (in this case we cannot derive 'Tense' property from the auxiliary verb)
        #
        # "will play" - "will be playing"
        if (error_future == corr_future or tense[0] == corr_tense[0]):
            if (len(aspect) and not len(corr_aspect) and aspect[0] == 'Prog') or \
                    (not len(aspect) and len(corr_aspect) and corr_aspect[0] == 'Prog'):
                return "Choice of tense"

    def check_voice(self):
        # TODO
        return "Voice"

    def check_modals(self, error, correction):
        if self.is_modal(error) and self.is_modal(correction) and error['token'] != error['token']:
            return "Modals"

    def check_noun_number(self):
        corr_number = []

        error_morph = self.error_properties['token_morph']
        error_number = error_morph.get('Number')

        correction = self.match_correction(self.error_properties, 0)
        if len(correction.keys()) != 0:
            corr_morph = correction['token_morph']
            corr_number = corr_morph.get('Number')

        if len(error_number) != 0 and len(corr_number) != 0 and error_number[0] != corr_number[0]:
            return "Noun number"

    def check_noun(self):
        if self.check_agreement_subjects():
            return "Agreement"
        return self.check_noun_number()
