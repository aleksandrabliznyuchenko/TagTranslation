from dictionaries import irregular_verbs


class Rules:
    modals = ['MD', 'VM0']
    preposition_tags = ['PRF', 'PRP', 'ADP', 'IN']

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
        self.sentence_dict = {}
        self.error_properties = {}
        self.correction_properties = {}
        self.full_error = {}
        self.current_token_id = None

    def match_correction(self, error_properties, mode):
        # POS-tag + TreeTagger tag: 'number' - 'number' / 'member'
        if mode == 0:
            for corr_id, correction in self.correction_properties.items():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_tag'] == error_properties['token_tag']:
                    return corr_id, correction

        # POS-tag: 'number' - 'number' / 'member' / 'amounts'
        elif mode == 1:
            for corr_id, correction in self.correction_properties.items():
                if correction['token_pos'] == error_properties['token_pos']:
                    return corr_id, correction

        # 'get' - 'getting'; POS-tag: VERB or AUX
        elif mode == 2:
            for corr_id, correction in self.correction_properties.items():
                if correction['token_pos'] == 'VERB' or correction['token_pos'] == 'AUX' or \
                        (correction['token_pos'] == 'NOUN' and correction['token'].endswith('ing')):
                    return corr_id, correction

        # modals
        elif mode == 3:
            for corr_id, correction in self.correction_properties.items():
                if self.is_modal(correction):
                    return corr_id, correction

        # POS-tag + TreeTagger tag + lemma: 'number' - 'number'
        else:
            for corr_id, correction in self.correction_properties.items():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_tag'] == error_properties['token_tag'] and \
                        correction['token_lemma'] == error_properties['token_lemma']:
                    return corr_id, correction
        return None, {}

    '''
    Checking word properties (it's part of speech, correct particle form of a verb etc.)
    '''

    def predicate_is_analytical(self, token_aux):
        head_id = token_aux['token_head']
        if head_id in self.full_error['tokens'].keys():
            head = self.full_error['tokens'][head_id]
            head_morph = head['token_morph']
            participle = head_morph.get('VerbForm')
            return head['token_dep'] == 'ROOT' and participle and participle[0] == 'Part'

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
                            child = self.sentence_dict[c[1]]
                            if child['token_pos'] == 'AUX':
                                return True

                elif token['token_pos'] == 'ADJ' and token['token'].endswith('ed') and \
                        len(token['ancestor_list']):
                    for a in token['ancestor_list']:
                        ancestor = self.sentence_dict[a[1]]
                        if ancestor['token_pos'] == 'AUX':
                            return True

        else:
            # full passive construction in the correction span
            # "is built", "was built", "will be built"
            for correction in self.correction_properties.values():
                if correction['token_pos'] == 'VERB':
                    aspect = correction['token_morph'].get('Aspect')
                    # "(is) argued" can be annotated either as a participle or a finite verb in the past
                    if ((aspect and aspect[0] == 'Perf' and self.is_participle(correction)) or
                            correction['token'].endswith('ed')):
                        if len(correction['children_list']):
                            for c in correction['children_list']:
                                child = self.correction_properties[c[1]]
                                if child['token_pos'] == 'AUX':
                                    return True

                        # if there is no full passive construction in the correction area,
                        # we try to reconstruct it from the sentence, examining dependencies of error token
                        #
                        # "(is) applying" (error) - "(is) applied" (correction)
                        error_token = self.error_properties
                        if len(error_token['children_list']):
                            for c in error_token['children_list']:
                                child = self.sentence_dict[c[1]]
                                if child['token_pos'] == 'AUX':
                                    return True

                elif correction['token_pos'] == 'ADJ' and correction['token'].endswith('ed'):
                    if len(correction['ancestor_list']):
                        for a in correction['ancestor_list']:
                            ancestor = self.correction_properties[a[1]]
                            if ancestor['token_pos'] == 'AUX':
                                return True

                    # if there is no full passive construction in the correction area,
                    # we try to reconstruct it from the sentence, examining dependencies of error token
                    #
                    # "(is) applying" (error) - "(is) applied" (correction)
                    error_token = self.error_properties
                    if len(error_token['ancestor_list']):
                        for a in error_token['ancestor_list']:
                            ancestor = self.sentence_dict[a[1]]
                            if ancestor['token_pos'] == 'AUX':
                                return True
        return False

    def is_modal(self, token):
        return token['token'] == 'will' or \
               (token['token_pos'] == 'AUX' and token['token_tag'] in self.modals)

    def is_finite_verb(self, token):
        verb_form = token['token_morph'].get('VerbForm')
        if verb_form:
            return (verb_form[0] == 'Fin' or verb_form[0] == 'Inf')
        return False

    def is_participle(self, token):
        verb_form = token['token_morph'].get('VerbForm')
        if verb_form:
            return verb_form[0] == 'Part'
        return False

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

    def is_infinitive(self, token):
        if self.is_finite_verb(token) and len(token['children_list']):
            for child in token['children_list']:
                if child[0] == 'to':
                    return True
        return False

    '''
    Checking word form (and whether a form of a word is correct or not)
    '''

    def token_in_correction(self, mode, missing=True):
        for correction in self.correction_properties.values():
            # articles
            if mode == 1:
                if correction['token'] in ['a', 'an', 'the']:
                    return False if missing else True
            # modals
            elif mode == 2:
                if self.is_modal(correction):
                    return False if missing else True

            elif mode == 3:
                if correction['token_tag'] in self.preposition_tags:
                    return False if missing else True

        return True if missing else False

    def check_irregular_form(self, form):
        irregular = irregular_verbs[self.error_properties['token_lemma']][form]
        return self.error_properties['token'] != irregular and self.correction_properties['token'] == irregular

    def check_verb_participle(self, error_token):
        check_correction = False

        # if we see the case of a verb controlling another verb, it is most likely a participle mistake
        # "feel encourage" - "feel encouraged"
        # "is applies" - "is applied"
        # "being develop" - "being developed"

        if self.is_finite_verb(error_token):
            # due to grammatical errors in such constructions they might be parsed differently,
            # so we have to check both children and ancestors of the error token
            if len(error_token['children_list']):
                child_id = error_token['children_list'][0][1]
                child = self.sentence_dict[child_id]
                # "is", "was", "were", "being" -- for some reason they end up as children of error token
                if child['token'] in self.aux or child['token'] == 'being':
                    check_correction = True

            if not check_correction and len(error_token['ancestor_list']):
                ancestor_id = error_token['ancestor_list'][0][1]
                ancestor = self.sentence_dict[ancestor_id]
                # gerund as ancestor ("feeling encourage") or
                # infinite verb as ancestor ("feel encourage")
                if ancestor['token_pos'] == 'VERB' \
                        and (self.is_gerund(ancestor) or
                             self.is_finite_verb(ancestor)):
                    check_correction = True

        if check_correction:
            for correction in self.correction_properties.values():
                if self.is_participle(correction):
                    return True
        return False

    def check_continuous(self, error_token, correction_token):
        # "(has) played" - "(has) been playing"
        # "(had) been playing" - "(had) played"
        if ((self.is_participle(error_token) and self.is_perfect(correction_token)) or
                (self.is_perfect(error_token) and self.is_participle(correction_token))):
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
                ancestor = self.sentence_dict[a[1]]
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
            ancestor = self.sentence_dict[ancestor_id]
            noun = ancestor['token_pos'] == 'NOUN'
            adj = ancestor['token_pos'] == 'ADJ'
            if noun or adj:
                for correction in self.correction_properties.values():
                    if self.is_participle(correction):
                        return True
        return False

    '''
    Rules that return tag matches
    '''

    def check_articles(self, error_token):
        # "a number" - "the number"
        # "number of the girls" - "number of girls"
        # "choose good film" - "choose a good film"

        if error_token['token'] in ['a', 'an', 'the']:
            _, correction_match = self.match_correction(error_token, 0)
            if correction_match and correction_match['token'] != error_token['token']:
                return 5  # Articles
            elif self.token_in_correction(mode=1, missing=True):
                return 5
        elif self.token_in_correction(mode=1, missing=False):
            return 5

    def check_modals(self, error_token):
        # "can allow" - "might allow"
        # "I rather agree" - "I would rather agree"

        if self.is_modal(error_token):
            _, correction_match = self.match_correction(error_token, 3)
            if correction_match and correction_match['token'] != error_token['token']:
                return 12  # Modals
            elif self.token_in_correction(mode=2, missing=True):
                return 12
        elif self.token_in_correction(mode=2, missing=False):
            return 12

    def check_prepositions(self, error_token):
        # TODO: Prepositional adverb (make a list of such adverbs?)

        # if the preposition is determined by the noun, the tag Prepositional noun is chosen;
        # if the preposition is determined by the adjective, the tag Prepositional adjective is chosen;
        # in other cases the preposition is independent and tag Prepositions is chosen
        #
        # "increase of" - "increase in" (Prepositional noun)
        # "regardless the loss" - "regardless of the loss" (Prepositional adjective)
        # "the growth increased for this period" - "the growth increased during this period" (Prepositions)

        if error_token['token_tag'] in self.preposition_tags:
            preposition_head = self.sentence_dict[error_token['token_head']]
            if preposition_head['token_pos'] == 'NOUN':
                tag = 18  # Prepositional noun
            elif preposition_head['token_pos'] == 'ADJ':
                tag = 25  # Prepositional adjective
            else:
                tag = 22  # Prepositions

            _, correction_match = self.match_correction(error_token, 1)
            if correction_match and correction_match['token'] != error_token['token']:
                return tag
            elif self.token_in_correction(mode=3, missing=True):
                return tag
        elif self.token_in_correction(mode=3, missing=False):
            if error_token['token_pos'] == 'NOUN':
                return 18  # Prepositional noun
            elif error_token['token_pos'] == 'ADJ':
                return 25  # Prepositional adjective
            else:
                return 22  # Prepositions

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

        _, correction = self.match_correction(error_token, 1)
        if correction:
            correction_morph = correction['token_morph']
            correction_number = correction_morph.get('Number')

        # is developing - develop; develop - have developed (Agreement + Choice of Tense)
        # look at her - is staring at her (Agreement + Choice of Tense + Choice of lexical item)
        else:
            if error_token['token_pos'] == 'VERB':
                for correction in self.correction_properties.values():
                    if correction['token_pos'] == 'AUX':
                        correction_morph = correction['token_morph']
                        correction_number = correction_morph.get('Number')
                        break
            elif error_token['token_pos'] == 'AUX':
                for correction in self.correction_properties.values():
                    if correction['token_pos'] == 'VERB' and not self.is_participle(correction):
                        correction_morph = correction['token_morph']
                        correction_number = correction_morph.get('Number')
                        break

        # morph of plural verbs has no 'Number' parameter
        if not correction_number:
            correction_number = ['Plur']

        if error_number != correction_number:
            return 32  # Agreement

    def check_agreement_subjects(self):
        # TODO: '_Mineral_ and chemicals are transported by road.' --> Subject Agreement instead of Noun Number error
        return ''

    def check_voice(self):
        # "builds" - "is built"
        # "built" - "is built" / "was built"
        # "will be discussed" - "will discuss"

        passive_error = self.passive_construction(correction=False)
        passive_correction = self.passive_construction(correction=True)

        if passive_error != passive_correction:
            return 11  # Voice

    def check_gerund_participle_pattern(self, error_token):
        _, correction_token = self.match_correction(error_token, 2)
        if correction_token:
            # "is applies" - "is applied"
            # "feel encourage" - "feel encouraged"

            if self.check_verb_pattern(error_token, correction_token):
                return 13  # Verb pattern

            if self.check_verb_participle(error_token):
                return 14  # Gerund or participle construction

            # "get" - "getting"
            if correction_token and not self.is_gerund(error_token) and self.is_gerund(correction_token):
                return 14  # Gerund or participle construction

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
        for corr_id, correction in self.correction_properties.items():
            if correction['token_pos'] == 'AUX':
                corr_morph = correction['token_morph']
                corr_tense = corr_morph.get('Tense')
                corr_mood = corr_morph.get('Mood')
                corr_aux = True
                break
        # if auxiliary verb is not found in the correction,
        # we simply look for the ROOT and take grammatical information from it
        if not corr_aux:
            for corr_id, correction in self.correction_properties.items():
                if correction['token_dep'] == 'ROOT':
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

    def check_verb(self, error_token):
        error, correction = {}, {}

        tag = self.check_gerund_participle_pattern(error_token)
        if tag:
            return tag

        tag, corr_id = self.check_tense_simple(error_token)
        if tag:
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
                ancestor = self.sentence_dict[a[1]]
                if ancestor['token_pos'] == 'VERB':
                    error = ancestor
                    _, correction = self.match_correction(ancestor, 1)
                    break

        if len(error.keys()) and len(correction.keys()) and \
                correction and self.check_continuous(error, correction):
            return 9  # Choice of tense

        # "materials produce in the country" - "materials produced in the country"
        # "prone to make mistakes" - "prone to making mistakes"
        tag = self.noun_adj_participle(error_token)
        if tag:
            return tag

    def check_noun_number(self):
        corr_number = []

        error_morph = self.error_properties['token_morph']
        error_number = error_morph.get('Number')

        _, correction = self.match_correction(self.error_properties, 1)
        if len(correction.keys()) != 0:
            corr_morph = correction['token_morph']
            corr_number = corr_morph.get('Number')

        if error_number and corr_number and error_number[0] != corr_number[0]:
            return 21  # Noun number

    def check_noun(self):
        if self.check_agreement_subjects():
            return 32  # Agreement
        return self.check_noun_number()
