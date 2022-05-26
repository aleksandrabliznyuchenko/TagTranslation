# TagTranslation
Translation of HEPTABOT error annotations into REALEC error tag system  
  
## Preprocessing  
  
Files from REALEC corpora (annotations and essay texts) are preprocessed in *preprocessing.py*. We form dictionaries of errors and tokens that are thoroughly examined later. The annotated essays are spell-checked and lowered.  
  
## Tag assignment  
  
After preprocessing, we proceed with tag assignment and form resulting annotation files in *process_files.py*.  
  
Tag assignment is done in *tag_matcher.py*. Class TagMatcher derives a set of rules that we apply to the error (*TagMatcher.define_rule*) and then applies them (*TagMatcher.apply_rule*). 
The list of rules is stored in *rules_base.py* and *rules.py*.  
  
*dictionary.py* contains some manually formed dictionaries that are used in some rules - like a list of irregular verbs with their forms.  
  
We also transform error and correction spans depending on the derived error tag - it is done in *error_span.py*.  
  
## SpaCy  
SpaCy parser and SpaCy custom tokeniser are kept in *spacy_tokenizer.py*  and *spacy_custom_tokeniser.py*  
  
## Folders
The only folder that you need to create to run the program successfully is the folder **Essays\Annotations**, where you should put both the texts of the essays and corresponding annotation files (either in one folder or a set of folders). The propgram will only process files that contain errors tagged with "gram", "comp" or "vocab" tags, other files will be left unchanged.    
The result annotation files will be stored in **Essays\Results** folder created by the program.  
