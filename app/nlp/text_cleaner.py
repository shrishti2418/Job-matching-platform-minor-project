import sys, os

# go up twice: nlp → app → Minor-Project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(BASE_DIR)

from app.utils import resume_parser

import re
import spacy


nlp = spacy.load("en_core_web_sm")

def clean_resume_text(text):
    """
    Cleans extracted resume text:
    - Converts to lowercase
    - Removes extra spaces, line breaks, and junk characters
    - Keeps emails, phone numbers, and addresses intact
    - Removes unwanted punctuation/symbols
    """
    # 1. Lowercase
    text = text.lower()

    # 2. Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # 3. Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text).strip()

    # 4. Remove unnecessary punctuation except @, . , - , + (useful for emails & phones)
    text = re.sub(r'[^a-z0-9@\.\-\+\s]', ' ', text)

    # 5. Process with spaCy for lemmatization & stopword cleaning (optional at this stage)
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_punct]

    return " ".join(tokens)

raw_text = resume_parser.extract_text_from_pdf("D:\\Minor-Project\\data\\resume1.pdf")
    
cleaned_text = clean_resume_text(raw_text)
print("Before Cleaning:\n", raw_text)
print("\nAfter Cleaning:\n", cleaned_text)

    

