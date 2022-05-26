import copy
import itertools
import os
import re

from spacy_tokenizer import SpacyTokenizer

nlp = SpacyTokenizer()

error_tags = ["gram", "vocab", "comp"]

temporary_folder = os.path.join(os.getcwd(), r'Essays\Temporary')
results_folder = os.path.join(os.getcwd(), r'Essays\Results')


def contains_errors(line):
    # if we see line with lemma in the beginning of the file, the file contains no mistakes
    # and we do not have to process it
    lemma_part = line.split('\t')[-1]
    if "lemma" in lemma_part:
        return 0
    return 1


def clear_lemma(lemma):
    lemma = lemma.replace("\'", '')
    return lemma


def is_normal(file):
    comment_pattern = re.compile(r"Cause T\d.*?")

    with open(file, 'r', encoding='utf-8') as f:
        lines = [line.replace('\n', '') for line in f.readlines()]
        if contains_errors(lines[1]) or contains_errors(lines[-1]):
            for line in lines:
                # we treat separately files with additional comments because of their structure
                line_part = line.split('\t')[-1]
                if re.match(comment_pattern, line_part) or "Dependent_change" in line_part:
                    return False
    return True


def fill_errors_dict(line1_parts, line2_parts):
    correction = 'Delete'

    error_id = line1_parts[0]
    error = line1_parts[2]
    gram_part = line1_parts[1].split()
    error_tag = gram_part[0]
    idx_1, idx_2 = int(gram_part[1]), int(gram_part[2])
    if len(line2_parts) > 2:
        correction = line2_parts[2]

    errors_dict = {
        'error': error,
        'error_id': error_id,
        'error_tag': error_tag,
        'correction': correction,
        'idx_1': idx_1, 'idx_2': idx_2,
    }
    return errors_dict


def fill_file_dict(line1_parts, line2_parts):
    token_id = line1_parts[0]
    token = line1_parts[2]
    tag_part = line1_parts[1].split()
    token_tag = tag_part[0]
    lemma_part = line2_parts[2].split(' = ')
    lemma = clear_lemma(lemma_part[1])
    idx_1, idx_2 = int(tag_part[1]), int(tag_part[2])

    tokens_dict = {
        'token': token,
        'token_id': token_id,
        'lemma': lemma,
        'token_tag': token_tag,
        'idx_1': idx_1, 'idx_2': idx_2,
    }
    return tokens_dict


def is_error(line_parts):
    error_tag = line_parts[1].split()[0]
    if error_tag in error_tags:
        return 1
    return 0


def is_token(line_parts):
    lemma_part = line_parts[-1].split(" = ")
    if "lemma" in lemma_part:
        return 1
    return 0


def ann_file_to_dicts(file):
    errors_dict, tokens_dict = {}, {}
    error_last_id, token_last_id = 0, 0

    with open(file, 'r', encoding='utf-8') as f:
        for line1, line2 in itertools.zip_longest(*[f] * 2):
            line1_parts = line1.replace('\n', '').split('\t')
            line2_parts = line2.replace('\n', '').split('\t') if line2 is not None else []

            if len(line2_parts):
                error_id, token_id = line1_parts[0], line2_parts[0]
            else:
                error_id, token_id = line1_parts[0], line1_parts[0]
            error_last_id = int(error_id[1:]) if int(error_id[1:]) > error_last_id else error_last_id
            token_last_id = int(token_id[1:]) if int(token_id[1:]) > token_last_id else token_last_id

            if is_error(line1_parts):
                errors_dict[error_id] = fill_errors_dict(line1_parts, line2_parts)
            elif len(line2_parts) and is_token(line2_parts):
                if not token_id and len(errors_dict.keys()) == 0:
                    return {}, {}
                tokens_dict[int(token_id[1:])] = fill_file_dict(line1_parts, line2_parts)
                token_last_id = int(token_id[1:]) if int(token_id[1:]) > token_last_id else token_last_id

    return errors_dict, tokens_dict, [error_last_id, token_last_id]


def error_in_sentence(errors_dict, sent_id, sent_idx):
    found = False
    for error_id, error in errors_dict.items():
        if error['idx_1'] >= sent_idx[0] and error['idx_2'] <= sent_idx[1]:
            errors_dict[error_id]['sentence_id'] = sent_id
            found = True
    return found


def derive_sentences(tokens_dict, errors_dict):
    sentences = {}
    idx_1, first_token = 0, 0

    last_error_id = list(errors_dict.keys())[-1]
    last_error_idx = errors_dict[last_error_id]['idx_2']
    for key, value in errors_dict.items():
        if value['idx_2'] > last_error_idx:
            last_error_idx = value['idx_2']

    for token in tokens_dict.values():
        if not first_token:
            idx_1 = token['idx_1']
            first_token = 1
        if token['token_tag'] == 'SENT':
            sentence_id = len(sentences.keys())
            if error_in_sentence(errors_dict, sentence_id, [idx_1, token['idx_2']]):
                sentences[sentence_id] = [idx_1, token['idx_2']]
            if token['idx_2'] > last_error_idx:
                break
            first_token = 0

    return sentences, errors_dict


def check_capitalisation(error, correction):
    for i, word in enumerate(error.split()):
        if word.isalpha() and len(correction.split()) >= i + 1:
            corr_word = correction.split()[i]
            if word != corr_word and (word == corr_word.capitalize() or word.capitalize() == corr_word):
                return 1
    return 0


def normalise(file_txt, errors, sentences):
    capitals = {}
    prev_difference = 0

    with open(file_txt, 'r', encoding='utf-8') as txt:
        text = txt.read()

        for error in errors.values():
            if error['error_tag'] in ['spell', 'Spelling'] and 'sentence_id' in error.keys():
                idx_1, idx_2 = error['idx_1'], error['idx_2']
                len_difference = len(error['correction']) - (idx_2 - idx_1)
                if prev_difference:
                    idx_1 += prev_difference
                    idx_2 += prev_difference

                # text = text[:idx_1] + error['correction'] + text[idx_2 + 1:]
                text = text[:idx_1] + error['correction'] + text[idx_2:]
                prev_difference += len_difference
                if len_difference != 0:
                    for sent_id, sentence in sentences.items():
                        if sent_id >= error['sentence_id']:
                            if sent_id > error['sentence_id']:
                                sentence[0] = sentence[0] + len_difference
                            sentence[1] = sentence[1] + len_difference
            if check_capitalisation(error['error'], error['correction']):
                capitals[error['error_id']] = error

        text = text.lower()
        return text, capitals, sentences


def first_tokens(tokens_dict, sent_dict):
    first_token_idx = [sent_idx[0] for sent_idx in sent_dict.values()]
    tokens = []

    for token_id, token in tokens_dict.items():
        if token['idx_1'] in first_token_idx:
            tokens.append(token_id)
    return tokens


def combine_two_dicts(tokens, spacy_dict, tokens_dict, errors_dict):
    total_dict = {}

    for i, first_token in enumerate(tokens):
        sentence = spacy_dict[i]
        for token_sent_id, token_sent in sentence.items():
            token_id = token_sent_id + first_token
            if token_id in tokens_dict.keys():
                token = sentence[token_sent_id]['token']
                token_ann = tokens_dict[token_id]['token'].lower()
                if token == token_ann:
                    sentence[token_sent_id]['token_tag'] = tokens_dict[token_id]['token_tag']
                    sentence[token_sent_id]['token_id_ann'] = tokens_dict[token_id]['token_id']
                    sentence[token_sent_id]['lemma_ann'] = tokens_dict[token_id]['lemma']

                    idx_1, idx_2 = tokens_dict[token_id]['idx_1'], tokens_dict[token_id]['idx_2']
                    sentence[token_sent_id]['idx_1'] = idx_1
                    sentence[token_sent_id]['idx_2'] = idx_2

                    for error_id, error in errors_dict.items():
                        if 'sentence_id' in error.keys():
                            if error['sentence_id'] == i and \
                                    error['idx_1'] <= idx_1 and error['idx_2'] >= idx_2:
                                sentence[token_sent_id]['error'] = error_id
                                break
        total_dict[i] = sentence

    return total_dict


def process_normal_file(ann_file, txt_file, filename, folder):
    total_dict, sent_dict = {}, {}
    errors_dict, tokens_dict, last_ids = ann_file_to_dicts(ann_file)

    if len(errors_dict.keys()) != 0:
        sentences_data, errors_dict = derive_sentences(tokens_dict, errors_dict)
        tokens = first_tokens(tokens_dict, sentences_data)
        text, capitals, updated_sent_data = normalise(txt_file, errors_dict, copy.deepcopy(sentences_data))

        # combine the dict of tokens with dict of spaCy tokens
        spacy_text_dict, sent_dict = nlp.spacy_dict(text, updated_sent_data)
        total_dict = combine_two_dicts(tokens, spacy_text_dict, tokens_dict, errors_dict)

        for sent_id in sent_dict.keys():
            sent_dict[sent_id]['idx_1'] = sentences_data[sent_id][0]
            sent_dict[sent_id]['idx_2'] = sentences_data[sent_id][1]

        if len(capitals.keys()) != 0:
            capitalisation_to_result_file(capitals, filename, folder, ann_file)

    return errors_dict, total_dict, sent_dict, last_ids


def capitalisation_to_result_file(errors, filename, folder, ann_file):
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    current_folder = os.path.join(results_folder, folder)
    if not os.path.exists(current_folder):
        os.makedirs(current_folder)

    max_error = 0
    for error in errors.keys():
        error_num = int(error[1:])
        if error_num > max_error:
            max_error = error_num
    max_error = max_error * 2

    result_filename = os.path.join(current_folder, filename + '.ann')
    with open(result_filename, 'w', encoding='utf-8') as result:
        with open(ann_file, 'r', encoding='utf-8') as ann:
            lines = ann.readlines()
            for i, line in enumerate(lines):
                if i > max_error:
                    result.write(line)
                    continue
                error_id = line.split('\t')[0]
                if error_id in errors.keys():
                    line_parts = line.split('\t')
                    tag_parts = line_parts[1].split()
                    tag_parts[0] = "Capitalisation"
                    new_tag_parts = ' '.join(tag_parts)
                    line_parts[1] = new_tag_parts
                    line = '\t'.join(line_parts)
                result.write(line)


def create_tmp_file(filename, ann_file):
    comment_pattern = re.compile(r"Cause T\d.*?")

    new_file = os.path.join(temporary_folder, filename + '_tmp.ann')
    with open(new_file, 'w', encoding='utf-8') as tmp_file:
        with open(ann_file, 'r', encoding='utf-8') as ann:
            for line in ann.readlines():
                line_part = line.split('\t')[-1]
                if not re.match(comment_pattern, line_part) and not "Dependent_change" in line_part:
                    tmp_file.write(line)
    return new_file


def preprocess_file(file, folder, filename):
    file_txt = file.split('.')[0] + '.txt'

    # file without additional comments
    if is_normal(file):
        errors_dict, tokens_dict, sent_dict, last_ids = process_normal_file(file, file_txt, filename, folder)

    # file with additional comments
    else:
        tmp_file = create_tmp_file(filename, file)
        errors_dict, tokens_dict, sent_dict, last_ids = process_normal_file(tmp_file, file_txt, filename, folder)
        os.remove(tmp_file)

    return errors_dict, tokens_dict, sent_dict, last_ids
