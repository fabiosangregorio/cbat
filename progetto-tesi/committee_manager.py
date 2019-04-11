headings = ["committee", "commission"]
program_headings = ["program", "programme"]

p_program_headings = [f'{ph} {h}' for h in headings for ph in program_headings]


# gets all the sections referring to a program committee
def extract_program_sections(text):
    if not text:
        return []

    program_indexes = list()
    for p in p_program_headings:
        for idx in findall(p, text.lower()):
            i_newline = text.find('\n', idx)
            if i_newline == -1:
                continue
            # this means that the current and the next heading are on the 
            # same line (e.g. Program committe chair)
            if (not any(h in text[idx+len(p):i_newline].lower() for h in 
                headings + ['chair'])):
                program_indexes.append(i_newline)

    sections = list()
    for start in program_indexes:
        next_headings = [text[start:].lower().find(p) for p in headings + ['chair']
            if text[start:].lower().find(p) > -1]
        next_heading = min(next_headings) if len(next_headings) else -1
        if next_heading > -1:
            end = text.rfind("\n", start, start+next_heading)
            if end == -1:
                continue
        else:
            end = len(text)
            
        if end - start > 5:
            # re-polish html to avoid misprints from the substring process
            sections.append(webutil.polish_html(text[start:end]))
    return sections


# extracts person name based on probablepeople or, alternatively, 
# based on most common name formats
def _extract_person_name(name):
    person = None
    try: # probablepeople name extraction
        pp_result = pp.tag(name)
    except: # pp either thinks the name is a company name or can't extract it
        pp_result = [None, None]

    if(pp_result[1] == "Person"):
        r = pp_result[0]
        r = {k: i.replace('(', '').replace(')', '') for k, i in r.items()}
        person = Author(
            fullname=name,
            firstname=r.get('GivenName'),
            middlename=r.get('MiddleName') or r.get('MiddleInitial') or
                       r.get('Nickname'),
            lastname=r.get('LastName') or r.get('Surname'))
    else:
        person = Author(fullname=name)

    # if pp can't extract name and surname, try an extraction based on most 
    # common name formats
    if not person.firstname or not person.lastname:
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

    # if I cant extract the name from the text, discard the person
    if not person.firstname or not person.lastname:
        return None

    return person


# FIXME: improve memory usage. Check how much RAM the model needs and figure out 
# which components are needed
# See: https://stackoverflow.com/questions/38263384/how-to-save-spacy-model-onto-cache
# See: https://github.com/explosion/spaCy/issues/3054
# Reply to https://stackoverflow.com/questions/54625341/how-to-solve-memory-error-while-loading-english-module-using-spacy
def extract_committee(cfp, nlp):
    text = cfp.cfp_text
    # threshold over which we can say the NER lost a significant amount of names
    loss_threshold = 0.7
    program_sections = _extract_program_sections(webutil.polish_html(text))

    # no program committee in CFP text, search in the external link
    if len(program_sections) == 0:
        text = _search_external_cfp(cfp.external_source)
        program_sections = _extract_program_sections(webutil.polish_html(text))

    program_committee = list()
    for section in program_sections:
        n_section_people = list()
        step = 0
        text_lines = section.splitlines()
        # run NER every `step` + offset lines and check if the result set is 
        # significantly reduced
        while True:
            n_step_people = list()

            for offset in range(0, step + 1):
                n_people = 0
                step_lines = [l for i, l in enumerate(text_lines) if (
                    len(l) >= 4 and i % (step + 1) == offset)]
                # NER multiprocessing on single lines
                for doc in nlp.pipe(step_lines, n_threads=16, batch_size=10000):
                    if len([e.text for e in doc.ents if e.label_ == 'PERSON']):
                        n_people += 1

                n_step_people.append(n_people)
            
            n_section_people.append(n_step_people)
            info(f'NER results with step {step + 1}: {n_section_people[step]}')

            if(max(n_section_people[step]) < loss_threshold * max([max(i) 
                for i in n_section_people])):
                break
            step += 1
            if step > 3:
                return []

        # run regex on the right `step` and offset set
        offset = n_section_people[-1].index(max(n_section_people[-1]))
        regex = re.compile(r"^\W*([\()\"\w\. '’-]+)", re.MULTILINE)
        
        section_people = list()
        for i in range(offset, len(text_lines), step):
            name = regex.search(text_lines[i]).group(1).strip()
            if step == 1:
                affiliation = text_lines[i].replace(name, "").strip(
                    string.punctuation + " ")
            else:
                affiliation = ', '.join(text_lines[(i + 1):(i + step)])

            affiliation_country = None
            # IMPROVE: names and affiliation could also be separated by "-"
            # note: the names could contain a "-"
            aff_splitted = affiliation.split(',')
            if len(aff_splitted) > 1:
                affiliation_country = aff_splitted.pop().strip()
                affiliation = ", ".join(aff_splitted)

            person = _extract_person_name(name)
            if not person:
                continue
            person.affiliation = affiliation
            person.affiliation_country = affiliation_country
            section_people.append(person)

        '''
        if more than half of the people were not extracted correctly, it means 
        that the section probably didn't contain people names *only*, therefore 
        we keep only the ones we are sure that are real people (and not 
        something else extracted as a person).
        '''
        n_not_exact = len([True for p in section_people if not p.exact])
        if n_not_exact / len(section_people) > 0.5:
            p_to_add = [p for p in section_people if p.exact]
            if p_to_add:
                program_committee.append(p_to_add)
        else:
            program_committee += section_people
    
    return program_committee