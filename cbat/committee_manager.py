from logging import info
import re
import string

import probablepeople as pp

from config import HEADINGS, P_PROGRAM_HEADINGS, NER_LOSS_THRESHOLD
from util.helpers import findall, printl
from util.webutil import polish_html
from models import Author


def extract_program_sections(text):
    """Gets all the sections referring to a program committee"""
    if not text:
        return []

    program_indexes = list()
    for p in P_PROGRAM_HEADINGS:
        for idx in findall(p, text.lower()):
            i_newline = text.find('\n', idx)
            if i_newline == -1:
                continue
            t = text[idx+len(p):i_newline].lower()
            if (not any(h in t for h in HEADINGS + ['chair'])
               and r'\(.*chair.*\)' not in t):
                # this means that the current and the next heading are on the
                # same line (e.g. Program committe chair)
                program_indexes.append(i_newline)

    sections = list()
    for start in program_indexes:
        next_headings = []
        re_chair = re.compile('\(.*chair.*\)')
        # get next heading skipping the word "(chair)", as it is often appended
        # at the end of a program committee member's name to symbolize he's also
        # a program chair.
        for p in (HEADINGS + ['chair']):
            nh = text[start:].lower().find(p)
            chairs = re_chair.search(text[start+nh-10+9:start+nh+10].lower())
            if (nh > -1 and not chairs):
                next_headings.append(nh)

        next_heading = min(next_headings) if len(next_headings) else -1
        if next_heading > -1:
            end = text.rfind("\n", start, start+next_heading)
            if end == -1:
                continue
        else:
            end = len(text) - 1

        if end - start > 5:
            # re-polish html to avoid misprints from the substring process
            sections.append(polish_html(text[start:end]))
    return sections


def _extract_person_name(name):
    """
    Extracts person name based on probablepeople or, alternatively, based on
    most common name formats.
    """
    person = None
    try:  # probablepeople name extraction
        pp_result = pp.tag(name)
    except Exception:  # pp either thinks the name is a company name or can't extract it
        pp_result = [None, None]

    if(pp_result[1] == "Person"):
        r = pp_result[0]
        r = {k: i.replace('(', '').replace(')', '') for k, i in r.items()}
        person = Author(
            fullname=name,
            firstname=r.get('GivenName'),
            middlename=(r.get('MiddleName') or
                        r.get('MiddleInitial') or
                        r.get('Nickname')),
            lastname=r.get('LastName') or r.get('Surname'))
    else:
        person = Author(fullname=name)

    if not person.firstname or not person.lastname:
        # if pp can't extract name and surname, try an extraction based on most
        # common name formats
        split_char = ',' if ',' in person.fullname else ' '
        splitted = person.fullname.split(split_char)

        first_word = splitted.pop(0).strip()
        last_words = " ".join(splitted).strip()
        if ',' in person.fullname:
            person.lastname = first_word
            person.firstname = last_words
        else:
            person.firstname = first_word
            person.lastname = last_words
        person.exact = False

    if not person.firstname or not person.lastname:
        # if I cant extract the name from the text, discard the person
        return None

    return person


def _extract_affiliation(affiliation):
    affiliation = affiliation.replace('(', '')
    affiliation = affiliation.replace(')', '')
    affiliation = affiliation.replace('"', '')
    affiliation = ''.join(x for x in affiliation if x in string.printable)

    affiliation_country = None
    # IMPROVE: names and affiliation could also be separated by "-"
    # note: the names could contain a "-"
    aff_splitted = affiliation.split(',')
    if len(aff_splitted) > 1:
        affiliation_country = aff_splitted.pop().strip()
        affiliation = ", ".join(aff_splitted)

    return affiliation, affiliation_country


def extract_committee(program_sections, nlp):
    # FIXME: improve memory usage. Check how much RAM the model needs and figure
    # out which components are needed
    # See: https://stackoverflow.com/questions/38263384/how-to-save-spacy-model-onto-cache
    # See: https://github.com/explosion/spaCy/issues/3054

    # threshold over which we can say the NER lost a significant amount of names
    loss_threshold = NER_LOSS_THRESHOLD
    program_committee = list()
    for section in program_sections:
        n_section_people = list()
        step = 0
        text_lines = section.splitlines()
        while True:
            printl('.')
            # run NER every `step` + offset lines and check if the result set is
            # significantly reduced
            n_step_people = list()

            for offset in range(0, step + 1):
                n_people = 0
                step_lines = [l for i, l in enumerate(text_lines) if (
                    len(l) >= 4 and i % (step + 1) == offset)]
                for doc in nlp.pipe(step_lines, n_threads=16, batch_size=10000):
                    # NER multiprocessing on single lines
                    if len([e.text for e in doc.ents if e.label_ == 'PERSON']):
                        n_people += 1

                n_step_people.append(n_people)

            n_section_people.append(n_step_people)
            info(f'NER results with step {step + 1}: {n_section_people[step]}')

            if(max(n_section_people[step]) < loss_threshold * max([max(i)
               for i in n_section_people])):
                info(f'Choosing step {step}')
                break
            step += 1
            if step > 3:
                return []

        # run regex on the right `step` and offset set
        # the offset is the offset with more results in the second-to-last run
        offset = n_section_people[-2].index(max(n_section_people[-2]))
        regex = re.compile(r"^\W*([\"\w\. '’]+)", re.MULTILINE)

        section_people = list()
        for i in range(offset, len(text_lines), step):
            results = regex.search(text_lines[i])
            name = results.group(1).strip() if results else ""
            STRIP_CHARS = string.punctuation + " ()-–"
            if step == 1:
                affiliation = text_lines[i].replace(name, "").strip(STRIP_CHARS)
            else:
                affiliation = ', '.join([l.strip(STRIP_CHARS) for l
                                        in text_lines[(i + 1):(i + step)]])

            affiliation, affiliation_country = _extract_affiliation(affiliation)
            person = _extract_person_name(name)
            if not person:
                continue
            person.affiliation = affiliation
            person.affiliation_country = affiliation_country

            section_people.append(person)

        n_not_exact = len([True for p in section_people if not p.exact])
        if n_not_exact / len(section_people) >= 0.5:
            # if more than half of the people were not extracted correctly, it
            # means that the section probably didn't contain people names only,
            # so we keep only the ones we are sure that are real people (and not
            # something else extracted as a person).
            p_to_add = [p for p in section_people if p.exact]
            if p_to_add:
                program_committee += p_to_add
        else:
            program_committee += section_people

    # return the program committee without duplicate authors
    seen = set()
    unique_committee = []
    for a in program_committee:
        compare = (a.getattr('fullname') + a.getattr('affiliation') +
                   a.getattr('affiliation_country'))
        if compare not in seen:
            unique_committee.append(a)
            seen.add(compare)

    if len(unique_committee) < 5:
        return []

    return unique_committee
