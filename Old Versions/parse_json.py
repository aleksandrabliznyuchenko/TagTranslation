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
tags = TagMatcher.tags


def form_new_lines(line1, line2, errors_with_tags):
    new_lines = ''

    line1_parts = line1.replace('\n', '').split('\t')
    line2_parts = line2.replace('\n', '').split('\t')

    error_id = line1_parts[0]
    tag_parts = line1_parts[1].split()
    ann_tag = ' '.join(tag_parts[:-2])
    ann_id = line2_parts[0]

    if len(errors_with_tags[error_id].keys()):
        if ann_tag == 'Capitalisation':
            new_lines += line1 + line2

        for token in errors_with_tags[error_id].values():
            if type(token) == dict and len(token.keys()):
                for tag_id, tag in token.items():
                    ann_tag = tag['tag']
                    error = tag['error_span'][0]
                    idx_1, idx_2 = str(tag['error_span'][1]), str(tag['error_span'][2])
                    correction = tag['correction']
                    ann_id = ann_id.split('_')[0] + '_' + str(tag_id)
                    # система нумерации переделана в итоговой версии

                    new_tag_parts = ' '.join([ann_tag, idx_1, idx_2])
                    new_ann_notes = 'AnnotatorNotes ' + str(error_id)

                    new_line_1 = '\t'.join([error_id, new_tag_parts, error]) + '\n'
                    new_line_2 = '\t'.join([ann_id, new_ann_notes, correction]) + '\n'
                    new_lines += new_line_1 + new_line_2

    if new_lines == '':
        new_lines += line1 + line2
    return new_lines


def fill_results(errors_with_tags, filename, folder, ann_file):
    errors_processed, skip_line = 0, 0
    ann_lines = ''

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    current_folder = os.path.join(results_folder, folder)
    if not os.path.exists(current_folder):
        os.makedirs(current_folder)

    last_error_id = list(errors_with_tags.keys())[-1]
    max_error = int(last_error_id[1:])

    ann_result_filename = Path(os.path.join(current_folder, filename + '_results.ann'))
    if ann_result_filename.exists():
        os.remove(ann_result_filename)

    with open(ann_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if skip_line:
                skip_line = 0
                continue
            if not errors_processed:
                line_id = line.replace('\n', '').split('\t')[0]
                if line_id[0] == 'T':
                    if int(line_id[1:]) == max_error:
                        errors_processed = 1
                    if line_id in errors_with_tags.keys():
                        ann_lines += form_new_lines(line1=line, line2=lines[i + 1],
                                                    errors_with_tags=errors_with_tags)
                        skip_line = 1
                    else:
                        ann_lines += line
                else:
                    ann_lines += line
            else:
                ann_lines += line
    file.close()

    with open(ann_result_filename, 'w', encoding='utf-8') as ann:
        ann.write(ann_lines)


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


def match_errors(errors_file, tokens_file, filename, folder, ann_file):
    errors_with_tags = {}

    with open(errors_file, 'r', encoding='utf-8') as errors_f:
        errors = json.load(errors_f)
    with open(tokens_file, 'r', encoding='utf-8') as tokens_f:
        tokens = str_keys_to_int(json.load(tokens_f))

    for error_id, error_value in errors.items():
        # TODO: добавить рассмотрение случаев, когда система удаляет элемент
        if error_value['correction'] != 'Delete':
            error_tokens = {}
            if 'sentence_id' in error_value.keys():
                sent_id = error_value['sentence_id']
                # for error in error_value['error'].lower().split():
                for error in error_value['error'].split():
                    for token_id, token in tokens[sent_id].items():
                        if 'error' in token.keys() and token['error'] == error_id and token['token'] == error.lower():
                            # key = [token_id, token['token_id_ann']]
                            error_tokens[token_id] = token
                            # error_tokens[token['token_id_ann']] = token
                error_value['tokens'] = error_tokens
                sentence_tokens = tokens[error_value['sentence_id']]

                # tag_set = matcher.match_tag(error_value, sentence_tokens)
                # errors_with_tags[error_id] = tag_set
                error_tags = matcher.match_tag(error_record=error_value, sentence_dict=sentence_tokens)
                errors_with_tags[error_id] = error_tags

    fill_results(errors_with_tags, filename, folder, ann_file)
    return 1


def process_json_files():
    global processed_files, file_num_total

    parsed_filenames = []

    for root, dirs, files in os.walk(path):
        for folder in dirs:
            if folder == 'Negation':  # TODO: потом убрать
                current_path = os.path.join(path, folder)
                files = os.listdir(current_path)
                file_num_total += len(files)

                for file in files:
                    filename = '_'.join(file.split('.')[0].split('_')[:-1])
                    if filename not in parsed_filenames:
                        errors_file = filename + '_errors.json'
                        tokens_file = filename + '_tokens.json'

                        errors_path = Path(os.path.join(current_path, errors_file))
                        tokens_path = Path(os.path.join(current_path, tokens_file))

                        ann_file = Path(os.path.join(os.path.join(annotations_folder, folder), filename + '.ann'))
                        if ann_file.exists():
                            ok = match_errors(errors_path, tokens_path, filename, folder, ann_file)
                            if ok:
                                parsed_filenames.append(filename)

    processed_files = len(parsed_filenames)


process_json_files()

time_end = time.perf_counter() - time_start
print("Total time: %i minutes %i seconds" % (time_end // 60, time_end % 60))
print('Files processed: %i out of %i' % (processed_files, file_num_total / 3))
