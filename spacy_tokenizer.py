import spacy
import spacy_conll
from spacy_custom_tokenizer import custom_tokenizer


class SpacyTokenizer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_trf", disable=["ner"])
        self.nlp.tokenizer = custom_tokenizer(self.nlp)
        self.nlp.add_pipe("conll_formatter", after='parser')

    def spacy_sentence_dict(self, sentence):
        token_inx = 0
        sentence_structure_dict = {
            token_inx:
                {
                    'token': '',
                    'token_head': '',
                    'token_dep': '',
                    'token_morph': {},
                    'children_list': [],
                    'ancestor_list': []
                }
        }
        doc = self.nlp(sentence)
        for token in doc:
            sentence_structure_dict[token.i] = {
                'token': token.text, 'token_dep': token.dep_,
                'token_head': token.head.i,
                'token_lemma': token.lemma_,
                'token_pos': token.pos_, 'token_tag': token.tag_,
                'token_morph': token.morph,
                'children_list': [(child.text, child.i) for child in
                                  token.children],
                'ancestor_list': [(ancestor.text, ancestor.i) for ancestor in
                                  token.ancestors]
            }
        return sentence_structure_dict

    def spacy_dict(self, text, sentences):
        spacy_dict, sentences_dict = {}, {}

        for sent_id, sent_idx in sentences.items():
            idx_1, idx_2 = sent_idx[0], sent_idx[1]
            sentence = text[idx_1:idx_2]
            if sent_id not in sentences_dict.keys():
                sentences_dict[sent_id] = {}
            sentences_dict[sent_id]['sentence'] = sentence
            sentences_dict[sent_id]['idx_1'] = idx_1
            sentences_dict[sent_id]['idx_2'] = idx_2

            # tokenise our normalised sentence using spaCy custom tokeniser
            spacy_dict[sent_id] = self.spacy_sentence_dict(sentence)
        return spacy_dict, sentences_dict
