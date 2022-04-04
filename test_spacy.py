import spacy
import spacy_conll
from test_spacy_custom_tokenizer import custom_tokenizer


# nlp = spacy.load("en_core_web_sm")
# doc = nlp(sentence)
# for token in doc:
#     print(token.text, token.dep_, token.head.text, token.head.pos_,
#             [child for child in token.children])

class SpacyAnalyzer:
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


    def spacy_text_dict(self, text):
        sent_num = 0
        idx_1 = 0

        text_dict = {}
        sentences_dict = {}
        tokens = self.nlp(text)
        for sent in tokens.sents:
            sentence = sent.text.replace('\n', '')
            if sentence != '':
                structure_dict = self.spacy_sentence_dict(sentence)
                text_dict[sent_num] = structure_dict

                if not sent_num in sentences_dict.keys():
                    sentences_dict[sent_num] = {}
                sentences_dict[sent_num]['text'] = sentence
                sentences_dict[sent_num]['idx_1'] = idx_1
                sentences_dict[sent_num]['idx_2'] = idx_1 + len(sentence)
                idx_1 += len(sentence) + 1
                sent_num += 1
        return text_dict, sentences_dict


# test = SpacyAnalyzer()
# 
# sentence_struct_PP = test.spacy_sentence_dict("will study")
# for key, value in sentence_struct_PP.items():
#     print(key, value)


