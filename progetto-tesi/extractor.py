import spacy
from spacy import displacy
import en_core_web_md
import time


def test(dict, text):
    start_time = time.time()

    # strips whitespaces and only gets lines with text
    text = os.linesep.join([s for s in text.splitlines() if s.strip()])

    nlp = en_core_web_md.load()
    doc = nlp(text)
    people = [ee for ee in doc.ents if ee.label_ == 'PERSON']

    print(time.time() - start_time)
    return people
