import warnings
from logging import info, warning

from fuzzywuzzy import process, fuzz
from scopus import AuthorSearch, ScopusSearch, AbstractRetrieval, AuthorRetrieval

from models import Author, Paper, Conference




# IMPROVE: use API 'field' attribute to only return used fileds

# IMPROVE: Many times the affiliation makes the search yield no result bc it 
# doesn't match perfectly, maybe try to search only for firstname and lastname 
# and use levenshtein to get the right author
def find_author(author):
    score_threshold = 70
    aff = author.getattr('affiliation')
    query = "AUTHFIRST({}) AND AUTHLASTNAME({}) {}".format(
        author.getattr('firstname'),
        ' '.join(filter(None, [author.getattr('middlename'), 
            author.getattr('lastname')])),
        f"AND AFFIL({aff})" if aff else '')

    if not aff:
        return None

    # IMPROVE: if FIRSTNAME AND LASTNAME yields no results, try switching names
    possible_people = AuthorSearch(query).authors
    if not possible_people or not aff:
        # if there is no affiliation we can't be sure if it's the right person.
        return None
    
    # FIXME: I don't think this is right. This doesn't check the affilitation's
    # country
    aff_list = [f"{p.affiliation}, {p.country}" for p in possible_people]
    affiliation, fuzz_score = process.extractOne(author.affiliation, 
        aff_list, scorer=fuzz.token_set_ratio)
    if fuzz_score > score_threshold:
        author.eid_list = [p.eid for p in possible_people 
            if affiliation.lower() == f"{p.affiliation}, {p.country}".lower()]
    else:
        # info(f"{author.fullname}; {author.affiliation}; {', '.join(aff_list)}")
        # TODO: handle no affiliation and wrong affiliation
        return None

    # Get author's subject areas
    # IMPROVE: Currently I only check for the first subject area, due to inability
    # to get multiple eids in one query (I might hit the weekly API cap)
    author.subject_areas = [int(s.code) for s in 
        AuthorRetrieval(author.eid_list[0]).subject_areas]

    return author


# IMPROVE: filtrare i risultati tramite levenshtein, vedere se sono conference 
# o journals (quindi vol. o anno) e vedere se l'anno va bene come filtro
# IMPROVE: non tutte le conferences sono listate in scopus, ma possono avere le
# paper. es: https://dblp.org/db/conf/securecomm/securecomm2016.html
# quindi cercare anche su dblp le conference e cercare le paper su scopus
# TODO: refactor this method using the conference info from CONFNAME
def get_conference_papers(conference):
    query = f"SRCTITLE({conference.getattr('acronym')}) \
              AND PUBYEAR = {conference.getattr('year')}"

    documents = ScopusSearch(query, view="STANDARD")
    papers = [Paper(scopus_id=sid) for sid in documents.get_eids()]
    return papers


def extract_references_from_paper(paper):
    try:
        references = AbstractRetrieval(paper.scopus_id, view="REF").references
    except Exception:
        warning('Retrieval of references failed for eid ' + paper.scopus_id)
        return []

    if not references:
        return []

    eids = [f"9-s2.0-{auid.strip()}" for ref in references if ref.authors_auid
            for auid in ref.authors_auid.split('; ')]
    return eids
