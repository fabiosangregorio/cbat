import re
import time
import string
import probablepeople as pp

import en_core_web_md
import spacy
from models import Author

import webutil


def _extract_program_sections(text):
    start_time = time.time()
    
    program_headings = ["program committee", "program chair", "program commission"]
    headings = ["committee", "chair", "commission"]

    # gets all the sections referring to a program committee
    program_indexes = [text.lower().find(p) + len(p) for p in program_headings if text.lower().find(p) > -1]
    sections = list()
    for start in program_indexes:
        next_headings = [text[start:].lower().find(p) for p in headings if text[start:].lower().find(p) > -1]
        next_heading = min(next_headings) if len(next_headings) else len(text)
        end = text.rfind("\n", 0, start+next_heading)
        # re-polish html to avoid misprints from the substring process
        sections.append(webutil.polish_html(text[start:end]))

    print('Extraction of program committee: ', time.time() - start_time)
    return sections


# extract person name based on probablepeople or, alternatively, most common name formats
def _extract_person_name(name, affiliation):
    person = None
    try: # probablepeople name extraction
        pp_result = pp.tag(name)
        if(pp_result[1] == "Person"):
            person = Author(
                fullname=name,
                firstname=pp_result[0].get('GivenName'),
                middlename=pp_result[0].get('MiddleName') or pp_result[0].get('MiddleInitial'),
                lastname=pp_result[0].get('LastName'),
                affiliation=affiliation)
        else:
            raise Exception()
    except: # pp either thinks the name is a company name or can't extract it
        person = Author(fullname=name, affiliation=affiliation)

    # if pp can't extract name and surname, try an extraction based on most common name formats
    if not (person.firstname and person.lastname):
        # check the format based on the presence of a comma
        if ',' in person.fullname:
            splitted = person.fullname.split(',')
            person.lastname = splitted.pop(0).strip()
            person.firstname = " ".join(splitted).strip()
        else:
            splitted = person.fullname.split(' ')
            person.firstname = splitted.pop(0).strip()
            person.lastname = " ".join(splitted).strip()

    return person


# FIXME: improve memory usage. Check how much RAM the model needs and figure out which components are needed
# See: https://stackoverflow.com/questions/38263384/how-to-save-spacy-model-onto-cache
# See: https://github.com/explosion/spaCy/issues/3054
# Reply to https://stackoverflow.com/questions/54625341/how-to-solve-memory-error-while-loading-english-module-using-spacy
def extract_program_committee(text):
    program_sections = _extract_program_sections(webutil.polish_html(text))

    start_time = time.time()
    nlp = spacy.load('en_core_web_md', disable=['parser', 'tagger', 'parser', 'textcat', 'entity'])
    print('Loading NER: ', time.time() - start_time)

    results = list()
    
    for section in program_sections:
        ner_results = []
        step = 0
        text_lines = section.splitlines()
        # run NER every `step` lines and check if the result set is significantly reduced.
        while True:
            start_time = time.time()
            people = 0
            # NER multiprocessing on single lines
            step_lines = [l for i, l in enumerate(text_lines) if len(l) >= 4 and i % (step + 1) == 0]
            for doc in nlp.pipe(step_lines, n_threads=16, batch_size=10000):
                people = people + 1 if len([ee.text for ee in doc.ents if ee.label_ == 'PERSON']) else people

            ner_results.append(people)
            print('NER results with step', step + 1, ':  ', ner_results[step], time.time() - start_time)
            # 10%: threshold over which we can say the NER lost a significant amount of names
            if(ner_results[step]) < 0.9 * max(ner_results):
                break
            step += 1

        # run regex on the right `step` set
        regex = re.compile(r"^\W*([\w\. '’-]+)", re.MULTILINE)

        for i in range(0, len(text_lines), step):
            name = regex.search(text_lines[i]).group(1).strip()
            if step == 1:
                affiliation = text_lines[i].replace(name, "").strip(string.punctuation + " ")            
            else:
                affiliation = ', '.join(text_lines[(i + 1):(i + 1 + step - 1)])

            person = _extract_person_name(name, affiliation)
            results.append(person)
            
    return results
