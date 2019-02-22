from scopus import AuthorSearch


def find_author(person):
  query = f"AUTHFIRST({person.name}) AND AUTHLASTNAME({person.surname}) AND AFFIL({person.affiliation})"

  # Author(eid, surname, initials, givenname, affiliation, documents, affiliation_id, city, country, areas)
  possible_people = AuthorSearch(query).authors
  find_right_affiliation(person.affiliation, [f"{p.affiliation}, {p.country}" for p in possible_people])
  # fare levenshtein e vedere se ci sono persone uguali a quello con lo score piu alto


def find_right_affiliation(aff_to_find, aff_list):
    score_threshold = 70

    # more than one person with the same name, without affiliation. I can't be sure of which name is the right one.
    if len([a[0] for a in affiliations.items() if not len(a[1])]) > 1:
        return {
            "status": "error",
            "err": "multiple_no_affiliation"
        }

    _, fuzz_score, best_index = process.extractOne(person_to_find.affiliation, affiliations, scorer=fuzz.token_set_ratio)
    
    if fuzz_score > score_threshold or (len(affiliations) == 1 and fuzz_score == 0):
        # regular best match or only one match (no affiliation)
        result_message["result"] = people_list[best_index]
    else:
        return {
            "status": "error",
            "err": "wrong_affiliation",
            "is_exact": is_exact
        }
    
    return result_message


find_author("Xiaodong", "Lin", "University of Ontario Institute of Technology, Canada")
