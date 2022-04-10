import itertools
import json
import re
import time

import os
import shutil
from pathlib import Path

from test_spacy import SpacyAnalyzer
from spacy.tokens import MorphAnalysis

time_start = time.perf_counter()

path = os.path.join(os.getcwd(), r'Essays\Input')
temporary_folder = os.path.join(os.getcwd(), r'Essays\Temporary')
destination_folder = os.path.join(os.getcwd(), r'Essays\Processed')
results_folder = os.path.join(os.getcwd(), r'Essays\Results')
annotations_folder = os.path.join(os.getcwd(), r'Essays\Annotations')
correct_folder = os.path.join(os.getcwd(), r'Dataset\Correct')
other_tags_folder = os.path.join(os.getcwd(), r'Dataset\Other Tags')

file_num, file_num_correct, \
file_num_other_tags, file_num_total = 0, 0, 0, 0
error_tags = ["gram", "vocab", "comp"]

nlp = SpacyAnalyzer()


def contains_mistakes(line):
    # if we see line with lemma in the beginning of the file, the file contains no mistakes
    # and we do not have to process it
    lemma_part = line.split('\t')[-1]
    if "lemma" in lemma_part:
        return 0
    return 1


def clear_lemma(lemma):
    lemma = lemma.replace("\'", '')
    return lemma


def move_correct_file(filename, filepath_ann, filepath_txt, other_tag=0):
    global file_num_correct, file_num_other_tags
    folder = correct_folder if not other_tag else other_tags_folder

    ann_file = Path(os.path.join(folder, filename + '.ann'))
    txt_file = Path(os.path.join(folder, filename + '.txt'))

    if not ann_file.exists():
        shutil.move(filepath_ann, folder)
    if not txt_file.exists():
        shutil.move(filepath_txt, folder)

    if not other_tag:
        file_num_correct += 2
    else:
        file_num_other_tags += 2


def make_lists(path_folder):
    files_normal = []
    files_with_comments = []
    comment_pattern = re.compile(r"Cause T\d.*?")

    files = os.listdir(path_folder)
    for file in files:
        if file.split('.')[1] == 'ann':
            filepath = os.path.join(path_folder, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [line.replace('\n', '') for line in f.readlines()]
                if contains_mistakes(lines[1]) != 0:
                    for line in lines:
                        # we treat separately files with additional comments because of their structure
                        line_part = line.split('\t')[-1]
                        if re.match(comment_pattern, line_part):
                            files_with_comments.append(file)
                            break
                        if is_token(line.split('\t')):
                            files_normal.append(file)
                            break
                else:
                    f.close()
                    filepath_txt = filepath.split('.')[0] + '.txt'
                    move_correct_file(file, filepath, filepath_txt)
    return files_normal, files_with_comments


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
    errors_dict = {}
    tokens_dict = {}
    token_id = 0

    with open(file, 'r', encoding='utf-8') as f:
        for line1, line2 in itertools.zip_longest(*[f] * 2):
            line1_parts = line1.replace('\n', '').split('\t')
            line2_parts = line2.replace('\n', '').split('\t')

            if is_error(line1_parts):
                error_id = line1_parts[0]
                errors_dict[error_id] = fill_errors_dict(line1_parts, line2_parts)
            elif is_token(line2_parts):
                if not token_id and len(errors_dict.keys()) == 0:
                    return {}, {}
                tokens_dict[token_id] = fill_file_dict(line1_parts, line2_parts)
                token_id += 1
    return errors_dict, tokens_dict


# на данном этапе берем каждое слово в области ошибки, ищем его аналог из области исправления по индексу слова и сравниваем регистры
# хотя надо бы искать в области исправления слово с такой же леммой и так далее
def check_capitalisation(error, correction):
    for i, word in enumerate(error.split()):
        if word.isalpha() and len(correction.split()) >= i + 1:
            corr_word = correction.split()[i]
            if word != corr_word and (word == corr_word.capitalize() or word.capitalize() == corr_word):
                return 1
    return 0


def normalise(file_txt, errors):
    capitals = {}

    with open(file_txt, 'r', encoding='utf-8') as txt:
        text = txt.read()

        for error in errors.values():
            if error['error_tag'] in ['spell', 'Spelling']:
                idx_1, idx_2 = error['idx_1'], error['idx_2']
                text = text[:idx_1] + error['correction'] + text[idx_2 + 1:]

            if check_capitalisation(error['error'], error['correction']):
                capitals[error['error_id']] = error

        text = text.lower()
        return text, capitals


def combine_two_dicts(spacy_dict, tokens_dict, errors_dict):
    length = 0
    for sent_id in spacy_dict.keys():
        if sent_id != 0:
            length += len(spacy_dict[sent_id - 1].values())

        sentence_dict = spacy_dict[sent_id]
        for i in sentence_dict.keys():
            token_i = i + length
            if token_i in tokens_dict.keys():
                token = sentence_dict[i]['token']
                token_ann = tokens_dict[token_i]['token'].lower()
                if token == token_ann:
                    sentence_dict[i]['token_tag'] = tokens_dict[token_i]['token_tag']
                    sentence_dict[i]['token_id_ann'] = tokens_dict[token_i]['token_id']
                    sentence_dict[i]['lemma_ann'] = tokens_dict[token_i]['lemma']

                    idx_1, idx_2 = tokens_dict[token_i]['idx_1'], tokens_dict[token_i]['idx_2']
                    sentence_dict[i]['idx_1'] = idx_1
                    sentence_dict[i]['idx_2'] = idx_2

                    for error_id, error in errors_dict.items():
                        if error['sentence_id'] == sent_id and \
                            error['idx_1'] <= idx_1 and error['idx_2'] >= idx_2:
                            sentence_dict[i]['error'] = error_id

        spacy_dict[sent_id] = sentence_dict
    return spacy_dict


def modify_errors_dict(errors_dict, sentence_dict):
    for error_id, error in errors_dict.items():
        idx_1, idx_2 = error['idx_1'], error['idx_2']
        for sent_id, sentence in sentence_dict.items():
            if sentence['idx_1'] <= idx_1 and sentence['idx_2'] >= idx_2:
                errors_dict[error_id]['sentence_id'] = sent_id
                break
    return errors_dict


def my_default(obj):
    if isinstance(obj, MorphAnalysis):
        return str(obj)


def process_normal_file(ann_file, txt_file, filename, folder, is_tmp=0):
    global file_num

    destination = os.path.join(destination_folder, folder)
    if not os.path.exists(destination):
        os.makedirs(destination)

    errors_dict, tokens_dict = ann_file_to_dicts(ann_file)

    if len(errors_dict.keys()) != 0:
        text, capitals = normalise(txt_file, errors_dict)

        # tokenise our normalised text using spaCy custom tokeniser
        spacy_text_dict, sentences_dict = nlp.spacy_text_dict(text)

        errors_dict = modify_errors_dict(errors_dict, sentences_dict)

        # combine the dict of tokens with dict of spaCy tokens
        total_dict = combine_two_dicts(spacy_text_dict, tokens_dict, errors_dict)

        errors_file = os.path.join(destination, filename + '_errors.json')
        tokens_file = os.path.join(destination, filename + '_tokens.json')
        sentences_file = os.path.join(destination, filename + '_sent.json')

        with open(errors_file, 'w', encoding='utf-8') as new_errors_file:
            json.dump(errors_dict, new_errors_file)

        with open(tokens_file, 'w', encoding='utf-8') as new_tokens_file:
            json.dump(total_dict, new_tokens_file, default=my_default)

        with open(sentences_file, 'w', encoding='utf-8') as new_sent_file:
            json.dump(sentences_dict, new_sent_file)

        if len(capitals.keys()) != 0:
            capitalisation_to_result_file(capitals, filename, folder, ann_file)

        file_num += 2
        return 1

    elif not is_tmp:
        move_correct_file(filename, ann_file, txt_file, 1)


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

    result_filename = os.path.join(current_folder, filename + '_results.ann')
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

    new_filepath = os.path.join(temporary_folder, filename + '_tmp.ann')
    with open(new_filepath, 'w', encoding='utf-8') as tmp_file:
        with open(ann_file, 'r', encoding='utf-8') as ann:
            for line in ann.readlines():
                line_part = line.split('\t')[-1]
                if not re.match(comment_pattern, line_part):
                    tmp_file.write(line)
    return new_filepath


def process_files():
    global file_num_total

    for root, dirs, files in os.walk(path):
        for folder in dirs:
            file_num_total += len(os.listdir(os.path.join(path, folder)))
            files_normal, files_with_comments = make_lists(os.path.join(path, folder))

            for file in files_normal:
                filepath = os.path.join(os.path.join(path, folder), file)
                filename = file.split('.')[0]
                filepath_txt = os.path.join(os.path.join(path, folder), filename + '.txt')
                print('%s processing' % file)

                ok = process_normal_file(filepath, filepath_txt, filename, folder)
                if ok:
                    if not os.path.exists(os.path.join(annotations_folder, folder)):
                        os.makedirs(os.path.join(annotations_folder, folder))
                    shutil.move(filepath, os.path.join(annotations_folder, folder))
                    shutil.move(filepath_txt, os.path.join(annotations_folder, folder))

            for file in files_with_comments:
                filepath = os.path.join(os.path.join(path, folder), file)
                filename = file.split('.')[0]
                filepath_txt = os.path.join(os.path.join(path, folder), filename + '.txt')
                new_filepath = create_tmp_file(filename, filepath)
                print('%s processing' % file)

                ok = process_normal_file(new_filepath, filepath_txt, filename, folder, 1)
                os.remove(new_filepath)
                if ok:
                    if not os.path.exists(os.path.join(annotations_folder, folder)):
                        os.makedirs(os.path.join(annotations_folder, folder))
                    shutil.move(filepath, os.path.join(annotations_folder, folder))
                    shutil.move(filepath_txt, os.path.join(annotations_folder, folder))


process_files()

time_end = time.perf_counter() - time_start
print("Total time: %i minutes %i seconds" % (time_end // 60, time_end % 60))
print('Files processed: %i out of %i' % ((file_num + file_num_correct + file_num_other_tags) / 2,
                                         file_num_total / 2))
print('%i files with errors, %i with other tags, %i correct files' %
      (file_num / 2, file_num_other_tags / 2, file_num_correct / 2))
