from fuzzywuzzy import fuzz, process

from scopus import AuthorSearch, AuthorRetrieval

from helpers import printl


# IMPROVE: use API 'field' attribute to only return used fileds


def find_authors(authors):
    auths = list()
    printl('Getting authors')
    for author in authors:
        auths.append(find_author(author))
        printl('.')
    print(' Done')
    return list(filter(None, auths)), sum(True for a in auths if a is None)


def find_author(author):
    # IMPROVE: Many times the affiliation makes the search yield no result bc
    # it doesn't match perfectly, maybe try to search only for firstname and
    # lastname and use levenshtein to get the right author
    score_threshold = 70
    aff = author.getattr('affiliation')
    if not aff:
        return None

    query = "AUTHFIRST({}) AND AUTHLASTNAME({}) {}".format(
        author.getattr('firstname'),
        ' '.join(filter(None, [author.getattr('middlename'),
                 author.getattr('lastname')])),
        f"AND AFFIL({aff})" if aff else '')

    # IMPROVE: if FIRSTNAME AND LASTNAME yields no results, try switching names
    possible_people = AuthorSearch(query).authors
    if not possible_people or not aff:
        # if there is no affiliation we can't be sure if it's the right person.
        return None

    # FIXME: I don't think this is right. This doesn't check the affilitation's
    # country
    aff_list = [f"{p.affiliation}, {p.country}" for p in possible_people]
    affiliation, fuzz_score = process.extractOne(author.affiliation,
                                                 aff_list,
                                                 scorer=fuzz.token_set_ratio)
    if fuzz_score > score_threshold:
        author.eid_list = [p.eid for p in possible_people
                           if affiliation.lower() == f"{p.affiliation}, {p.country}".lower()]
    else:
        # TODO: handle no affiliation and wrong affiliation
        return None

    # Get author's subject areas
    # IMPROVE: Currently I only check for the first subject area, due to
    # inability to get multiple eids in one query (I might hit the API cap)
    author.subject_areas = [int(s.code) for s in
                            AuthorRetrieval(author.eid_list[0]).subject_areas]
    return author
