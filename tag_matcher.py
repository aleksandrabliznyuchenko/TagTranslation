from rules import Rules
from dictionaries import pos_dict


class TagMatcher:

    def __init__(self, nlp):
        self.nlp = nlp
        self.rules = Rules()

    def token(self, error_token, tokens):
        for token in tokens.values():
            if token['token'] == error_token.lower():
                return token
        return {}

    def match_correction(self, correction_properties, error_properties, mode):
        if mode == 0:
            for correction_id, correction in correction_properties.items():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_tag'] == error_properties['token_tag']:
                    return correction_id
        elif mode == 1:
            for correction_id, correction in correction_properties.items():
                if correction['token_pos'] == error_properties['token_pos']:
                    return correction_id
        else:
            for correction_id, correction in correction_properties.items():
                if correction['token_pos'] == error_properties['token_pos'] and \
                        correction['token_tag'] == error_properties['token_tag'] and \
                        correction['token_lemma'] == error_properties['token_lemma']:
                    return correction_id

    def article_in_correction(self):
        for correction in self.rules.correction_properties.values():
            if correction['token_dep'] == 'det':
                return True

    ###################################################################################################

    def define_rules(self, token_properties, matched_tags):
        rules = []

        token_dep = token_properties['token_dep']
        pos_tag = token_properties['token_pos']
        tag = token_properties['token_tag']

        if not "articles" in matched_tags and \
                (token_dep == "det" or self.article_in_correction()):
            rules.append("articles")

        # cases like "interest OF the game" --> "interest IN the game" (Prepositions)
        # TODO: cases like "carried" --> "carried out" (Verb pattern)
        if tag in self.rules.preposition_tags:
            rules.append("prepositions_simple")

        """
        For verbs we always check agreement with subject, because checking whether we should check it or not
        basically involves the check
        """
        if pos_tag == "VERB" or pos_tag == "AUX":
            if not self.rules.is_participle(token_properties):
                rules.append("agreement")
            if "Choice of tense" not in matched_tags:
                rules.append("choice_of_tense")

            if pos_tag == "AUX" and tag == "MD":
                rules.append("modals")

        elif pos_tag == "NOUN":
            if tag in pos_dict["NUM"]:
                rules.append("numerals")
            else:
                rules.append("noun_number")

        return rules

    def apply_rule(self, rule, error_token, correction):
        pos_tag = error_token['token_pos']
        tag = ''

        if rule == "articles":
            tag = self.rules.check_articles(error_token)

        elif rule == "prepositions_simple":
            correction_match = self.rules.match_correction(error_token, 1)
            if correction_match:
                tag = self.rules.check_prepositions_simple(error_token, correction_match)

        elif pos_tag == "VERB" or pos_tag == "AUX":
            if rule == "agreement":
                tag = self.rules.check_agreement_subject_pred(error_token)
            elif rule == "choice_of_tense":
                tag = self.rules.check_tense()
                if not tag:
                    # TODO Tense Form
                    tag = ""
            elif rule == "modals":
                tag = self.rules.check_modals(error_token, correction)

        elif pos_tag == "NOUN":
            if rule == "numerals":
                # TODO Numerals
                tag = "Numerals"
            elif rule == "noun_number":
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
        match = []
        token_id_max = 0

        error = error_record['error']
        self.rules.full_error = error_record
        self.rules.sentence_dict = sentence_dict

        for key in error_record['tokens']:
            if key > token_id_max:
                token_id_max = key

        # set new correction span if needed for spaCy to work more precisely
        # for example, from "the" to "the number" or from "have been" to "have been developing"
        correction = self.update_correction(correction=error_record['correction'],
                                            token_id=token_id_max,
                                            sentence_dict=sentence_dict)
        self.rules.correction_properties = self.nlp.spacy_sentence_dict(correction)

        for token_id, error_token in enumerate(error.split()):
            token = self.token(error_token=error_token, tokens=error_record['tokens'])

            # at this point we examine each token from the error span separately
            # if we encounter constructions like analytical predicates ("have done", "will be doing" etc),
            # the error will be broadened when the rule is applied
            self.rules.error_properties = token
            set_of_rules = self.define_rules(token, match)

            for rule in set_of_rules:
                tag = self.apply_rule(rule, token, correction)
                if tag:
                    match.append(tag)

        return match
