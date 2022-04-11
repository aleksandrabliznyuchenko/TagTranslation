import json
import os
from pathlib import Path
import time

from spacy.tokens import MorphAnalysis
from test_spacy import SpacyAnalyzer
from tag_matcher import TagMatcher

time_start = time.perf_counter()

path = os.path.join(os.getcwd(), r'Essays\Processed')
results_folder = os.path.join(os.getcwd(), r'Essays\Results')
annotations_folder = os.path.join(os.getcwd(), r'Essays\Annotations')

processed_files, file_num_total = 0, 0

nlp = SpacyAnalyzer()
matcher = TagMatcher(nlp)


def fill_result_file(errors_with_tags, filename, folder, ann_file):
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    current_folder = os.path.join(results_folder, folder)
    if not os.path.exists(current_folder):
        os.makedirs(current_folder)

    max_error = 0
    for error in errors_with_tags.keys():
        error_num = int(error[1:])
        if error_num > max_error:
            max_error = error_num
    max_error = max_error * 2

    result_filename = Path(os.path.join(current_folder, filename + '_results.ann'))

    if not result_filename.exists():
        with open(result_filename, 'w', encoding='utf-8') as result:
            with open(ann_file, 'r', encoding='utf-8') as ann:
                lines = ann.readlines()
                for i, line in enumerate(lines):
                    if i > max_error:
                        result.write(line)
                        continue
                    error_id = line.split('\t')[0]
                    if error_id in errors_with_tags.keys():
                        line_parts = line.split('\t')
                        tag_parts = line_parts[1].split()
                        error_tags = ' '.join(tag_parts[:-2])

                        if len(errors_with_tags[error_id]) != 0:
                            if error_tags == "Capitalisation":
                                error_tags = error_tags + ', ' + ', '.join(errors_with_tags[error_id])
                            else:
                                error_tags = ', '.join(errors_with_tags[error_id])
                        new_tag_parts = error_tags + ' ' + tag_parts[-2] + ' ' + tag_parts[-1]
                        line_parts[1] = new_tag_parts
                        line = '\t'.join(line_parts)
                    result.write(line)
    else:
        new_lines = ''
        with open(result_filename, 'r', encoding='utf-8') as result:
            lines = result.readlines()
            for i, line in enumerate(lines):
                if i > max_error:
                    new_lines += line
                    continue
                error_id = line.split('\t')[0]
                if error_id in errors_with_tags.keys():
                    line_parts = line.split('\t')
                    tag_parts = line_parts[1].split()
                    error_tags = ' '.join(tag_parts[:-2])

                    if len(errors_with_tags[error_id]) != 0:
                        if error_tags == "Capitalisation":
                            error_tags = error_tags + ', ' + ', '.join(errors_with_tags[error_id])
                        else:
                            error_tags = ', '.join(errors_with_tags[error_id])
                    new_tag_parts = error_tags + ' ' + tag_parts[-2] + ' ' + tag_parts[-1]
                    line_parts[1] = new_tag_parts
                    line = '\t'.join(line_parts)
                new_lines += line
            result.close()
        with open(result_filename, 'w', encoding='utf-8') as result_write:
            result_write.write(new_lines)


def str_keys_to_int(dictionary):
    value_dict = {}
    new_dictionary = {}
    iterate = True

    for key, value in dictionary.items():
        if iterate:
            if len(value.keys()) != 0:
                for key_value, value_value in value.items():
                    if not key_value.isdigit():
                        iterate = False
                        break
                    # transform morph from str back to MorphAnalysis
                    if 'token_morph' in value_value.keys():
                        value_value['token_morph'] = MorphAnalysis(nlp.nlp.vocab, value_value['token_morph'])
                    value_dict[int(key_value)] = value_value
            if len(value_dict.keys()) != 0:
                new_dictionary[int(key)] = value_dict
                value_dict = {}
        else:
            new_dictionary[int(key)] = value
    return new_dictionary


def match_errors(errors_file, tokens_file, sent_file, filename, folder, ann_file):
    errors_with_tags = {}

    with open(errors_file, 'r', encoding='utf-8') as f:
        errors = json.load(f)
    with open(tokens_file, 'r', encoding='utf-8') as tokens_f:
        tokens = str_keys_to_int(json.load(tokens_f))
    # with open(sent_file, 'r', encoding='utf-8') as sent_f:
    #     sentences = str_keys_to_int(json.load(sent_f))

    for error_id, error_value in errors.items():
        # пока что рассматриваем случаи, когда система предложила исправление, а не удалила элемент
        if error_value['correction'] != 'Delete':
            error_tokens = {}
            sent_id = error_value['sentence_id']
            for error in error_value['error'].lower().split():
                for token_id, token in tokens[sent_id].items():
                    if 'error' in token.keys() and token['error'] == error_id and token['token'] == error:
                        # key = [token_id, token['token_id_ann']]
                        error_tokens[token_id] = token
            error_value['tokens'] = error_tokens
            sentence_tokens = tokens[error_value['sentence_id']]

            tag_set = matcher.match_tag(error_value, sentence_tokens)
            errors_with_tags[error_id] = tag_set

    fill_result_file(errors_with_tags, filename, folder, ann_file)
    return 1


def process_json_files():
    global processed_files, file_num_total
    parsed_filenames = []

    for root, dirs, files in os.walk(path):
        for folder in dirs:
            # if folder == 'Test':  # TODO: потом убрать
            current_path = os.path.join(path, folder)
            files = os.listdir(current_path)
            file_num_total += len(files)

            for file in files:
                filename = '_'.join(file.split('.')[0].split('_')[:-1])
                if filename not in parsed_filenames:
                    errors_file = filename + '_errors.json'
                    tokens_file = filename + '_tokens.json'
                    sentences_file = filename + '_sent.json'

                    errors_path = Path(os.path.join(current_path, errors_file))
                    tokens_path = Path(os.path.join(current_path, tokens_file))
                    sentences_path = Path(os.path.join(current_path, sentences_file))

                    ann_file = Path(os.path.join(os.path.join(annotations_folder, folder), filename + '.ann'))
                    if ann_file.exists():
                        ok = match_errors(errors_path, tokens_path, sentences_path, filename, folder, ann_file)
                        if ok:
                            parsed_filenames.append(filename)

    processed_files = len(parsed_filenames)


process_json_files()

time_end = time.perf_counter() - time_start
print("Total time: %i minutes %i seconds" % (time_end // 60, time_end % 60))
print('Files processed: %i out of %i' % (processed_files, file_num_total / 3))
