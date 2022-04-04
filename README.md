# TagTranslation
Translation of HEPTABOT error annotations into REALEC error tag system  
  
## Preprocessing  
  
Files from REALEC corpora (annotations and essay texts) are preprocessed in *ann_to_json.py*. We form 3 new files in JSON-format from each essay and annotation. The essays are spell-checked and lowered.  
* *filename*_errors.json - contains all the errors with tags "gram", "comp", "vocab" found in the annotation file  
* *filename*_tokens.json - contains all the tokens from the annotation file with added spaCy morphological and syntactic data  
* *filename*_sents.json - contains the list of sentences from the essay text  
  
## Tag assignment  
  
JSON-files are processed in *parse_json.py*. This program parses the files, sends errors to the input of tag-matching program and writes the results of tag assignment to a new annotation file in the Essays/Results folder.  
  
Tag assignment is done in *tag_matcher.py*. Class TagMatcher derives a set of rules that we apply to the error (*TagMatcher.define_rule*) and then applies them (*TagMatcher.apply_rule*). 
The list of rules is stored in *rules.py*.  
  
*dictionary.py* contains some manually formed dictionaries that are used in some rules - like a list of irregular verbs with their forms.  
  
## SpaCy  
SpaCy parser and SpaCy custom tokeniser are kept in *test_spacy.py*  and *test_spacy_custom_tokeniser.py*  
  
## Folders
The essays from the corpora should be put in Essays\Test folder. Later the correct files (files containing no annotated errors) will be moved to Dataset\Correct folder; files containing annotations, but having no "gram", "comp" or "vocab" tags will be moved to Dataset\Other Tags folder.  
JSON-files will be put in Essays\Processed folder.  
The result annotation files can be found in Essays\Results folder.  
  
The annotations from the corpora which will later be used to form the result file are stored in Essays\Annotations folder.
