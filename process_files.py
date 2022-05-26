import os
from pathlib import Path
import time

from preprocessing import preprocess_file
from spacy_tokenizer import SpacyTokenizer
from tag_matcher import TagMatcher

time_start = time.perf_counter()

last_error_id, last_ann_id = 0, 0
file_num, file_num_total = 0, 0
used_error_ids = []

text = ''

path = os.path.join(os.getcwd(), r'Essays\Annotations')
results_folder = os.path.join(os.getcwd(), r'Essays\Results')

nlp = SpacyTokenizer()
matcher = TagMatcher(nlp)
tags = TagMatcher.tags


def result_txt_lines(orig_lines, idx, sent_idx):
    global text
    result_lines = ''

    idx_1, idx_2 = int(idx[0]), int(idx[1])
    sent_idx_1, sent_idx_2 = sent_idx[0], sent_idx[1]
    sentence_text = text[sent_idx_1:idx_1] + '<<' + text[idx_1:idx_2] + '>>' + text[idx_2:sent_idx_2]

    result_lines += 'Original ann sentence: %s\n\n' % sentence_text
    result_lines += 'Original ann record:\n' + orig_lines
    result_lines += 'Changed to:\n'

    return result_lines


def form_new_lines(line1, line2, errors_with_tags, sentences):
    global last_error_id, last_ann_id, used_error_ids
    new_lines, result_lines = '', ''
    new_error = 0

    line1_parts = line1.replace('\n', '').split('\t')
    line2_parts = line2.replace('\n', '').split('\t')

    error_id = line1_parts[0]
    tag_parts = line1_parts[1].split()
    idx_1, idx_2 = tag_parts[-2], tag_parts[-1]

    ann_tag = ' '.join(tag_parts[:-2])
    ann_id = line2_parts[0]

    if len(errors_with_tags[error_id].keys()):
        if ann_tag == 'Capitalisation':
            new_lines += line1 + line2
            new_error = 1
            last_error_id += 1
            last_ann_id += 1

        for token in errors_with_tags[error_id].values():
            if type(token) == dict and len(token.keys()):
                sentence = sentences[errors_with_tags[error_id]['sentence_id']]
                result_lines += result_txt_lines(orig_lines=line1 + line2,
                                                 idx=[idx_1, idx_2],
                                                 sent_idx=[sentence['idx_1'], sentence['idx_2']])

                for tag_idx, tag_id in enumerate(token.keys()):
                    tag = token[tag_id]
                    ann_tag = tag['tag']
                    error = tag['error_span'][0]
                    idx_1, idx_2 = str(tag['error_span'][1]), str(tag['error_span'][2])
                    correction = tag['correction']

                    if tag_idx > 0:
                        new_error = 1
                        last_error_id += 1
                        last_ann_id += 1

                    # new_error_id = 'T' + str(last_error_id) if tag_idx > 0 else error_id
                    # new_ann_id = '#' + str(last_ann_id) if tag_idx > 0 else ann_id
                    new_error_id = 'T' + str(last_error_id) if new_error else error_id
                    new_ann_id = '#' + str(last_ann_id) if new_error else ann_id

                    new_tag_parts = ' '.join([ann_tag, idx_1, idx_2])
                    new_ann_notes = 'AnnotatorNotes ' + str(new_error_id)

                    new_line_1 = '\t'.join([new_error_id, new_tag_parts, error]) + '\n'
                    new_line_2 = '\t'.join([new_ann_id, new_ann_notes, correction]) + '\n'
                    new_lines += new_line_1 + new_line_2
                    result_lines += new_line_1 + new_line_2 + '\n'
                    used_error_ids.append(new_error_id)

    return new_lines, result_lines + '\n' if result_lines != '' else ''


def fill_results(errors_with_tags, filename, folder, ann_file, sentences):
    global file_num_total, used_error_ids
    errors_processed, skip_line, max_error = 0, 0, 0
    ann_lines = ''
    used_error_ids = []

    if len(errors_with_tags.keys()):
        last_error_id = list(errors_with_tags.keys())[-1]
        max_error = int(last_error_id[1:])
    else:
        errors_processed = 1

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    current_folder = os.path.join(results_folder, folder)
    if not os.path.exists(current_folder):
        os.makedirs(current_folder)

    output_file_name = Path(os.path.join(os.getcwd(), 'Exam2020_%s.txt' % folder))
    if output_file_name.exists() and file_num_total == 1:
        os.remove(output_file_name)
    results_txt = open(output_file_name, 'a', encoding='utf-8')
    results_txt.write('File:   %s\n\n\n' % filename)

    ann_result_filename = Path(os.path.join(current_folder, filename + '.ann'))
    file_to_read = ann_file if not ann_result_filename.exists() else ann_result_filename

    with open(file_to_read, 'r', encoding='utf-8') as file:
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
                        new_ann_lines, result_lines = form_new_lines(line1=line, line2=lines[i + 1],
                                                                     errors_with_tags=errors_with_tags,
                                                                     sentences=sentences)
                        ann_lines += new_ann_lines
                        skip_line = 1
                        results_txt.write(result_lines)
                    elif line_id in used_error_ids:
                        skip_line = 1
                    else:
                        ann_lines += line
                else:
                    ann_lines += line
            else:
                # If we have already edited the annotation file,
                # we could have added additional lines with error annotations to it.
                # (we do that when we detect more than one tag suitable for the error)
                #
                # When we rewrite the annotation, we form new additional lines and add them to the file.
                # Thus, we have to skip previously added lines so that we do not have double annotations.
                line_id = line.replace('\n', '').split('\t')[0]
                if line_id in used_error_ids:
                    skip_line = 1
                else:
                    ann_lines += line
    file.close()
    results_txt.close()

    with open(ann_result_filename, 'w', encoding='utf-8') as ann:
        ann.write(ann_lines)


def match_errors(errors, tokens, sentences, filename, folder, ann_file):
    errors_with_tags = {}

    for error_id, error_value in errors.items():
        if 'sentence_id' in error_value.keys():
            error_tokens = {}
            sent_id = error_value['sentence_id']

            for error in error_value['error'].split():
                for token_id, token in tokens[sent_id].items():
                    if 'error' in token.keys() and token['error'] == error_id and token['token'] == error.lower():
                        error_tokens[token_id] = token
            error_value['tokens'] = error_tokens
            sentence_tokens = tokens[error_value['sentence_id']]

            error_tags = matcher.match_tag(error_record=error_value, sentence_dict=sentence_tokens)
            errors_with_tags[error_id] = error_tags

    fill_results(errors_with_tags, filename, folder, ann_file, sentences)
    return 1


def process_files():
    global file_num_total, file_num, last_error_id, last_ann_id
    global text

    for root, dirs, files in os.walk(path):
        for folder in dirs:
            path_folder = os.path.join(path, folder)
            files = os.listdir(path_folder)
            for file in files:
                if file.split('.')[1] == 'ann':
                    filename = file.split('.')[0]
                    filepath = os.path.join(path_folder, file)
                    if contains_mistakes(filepath):
                        print('%s processing' % file)
                        file_num_total += 1

                        filepath_txt = filepath.split('.')[0] + '.txt'
                        with open(filepath_txt, 'r') as text_file:
                            text = text_file.read()
                        text_file.close()

                        try:
                            errors_dict, tokens_dict, sent_dict, last_ids = preprocess_file(filepath, folder,
                                                                                            filename)
                            if len(errors_dict.keys()):
                                last_error_id, last_ann_id = last_ids[0], last_ids[1]

                                ok = match_errors(errors=errors_dict, tokens=tokens_dict, sentences=sent_dict,
                                                  filename=filename, folder=folder, ann_file=filepath)
                                if ok:
                                    file_num += 1

                        except Exception as exc:
                            with open('logger.txt', 'a') as log:
                                log.write('File %s: %s' % (file, str(exc)) + '\n\n')
                                log.close()


def contains_mistakes(file):
    with open(file, 'r', encoding='utf-8') as f:
        first_line = f.readlines()[1]
        lemma_part = first_line.split('\t')[-1]
        if "lemma" in lemma_part:
            return False
        return True


process_files()

time_end = time.perf_counter() - time_start
print("Total time: %i minutes %i seconds" % (time_end // 60, time_end % 60))
print('Files processed: %i out of %i' % (file_num, file_num_total))
