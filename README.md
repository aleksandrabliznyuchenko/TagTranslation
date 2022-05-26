# TagTranslation
Translation of HEPTABOT error annotations into REALEC error tag system  
  
## Preprocessing  
  
Files from REALEC corpora (annotations and essay texts) are preprocessed in *preprocessing.py*. We form dictionaries of errors and tokens that are thoroughly examined later. The annotated essays are spell-checked and lowered.  
  
## Tag assignment  
  
After preprocessing, we proceed with tag assignment and forming result annotation files in *process_files.py*.  
  
Tag assignment is done in *tag_matcher.py*. Class TagMatcher derives a set of rules that we apply to the error (*TagMatcher.define_rule*) and then applies them (*TagMatcher.apply_rule*). 
The list of rules is stored in *rules_base.py* and *rules.py*.  
  
*dictionary.py* contains some manually formed dictionaries that are used in some rules - like a list of irregular verbs with their forms.  
  
We also transform error and correction spans depending on the derived error tag - it is done in *error_span.py*.  
  
## SpaCy  
SpaCy parser and SpaCy custom tokeniser are kept in *test_spacy.py*  and *test_spacy_custom_tokeniser.py*  
  
## Folders
The essays from the corpora should be put in **Essays\Annotations** folder in a separate folder or a set of folders. We will only process files that contain errors tagged with "gram", "comp" or "vocab" tags.    
The result annotation files can be found in **Essays\Results** folder.  
