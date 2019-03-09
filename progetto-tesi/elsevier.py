from scopus import AuthorSearch, ScopusSearch, AbstractRetrieval
from fuzzywuzzy import process, fuzz

from models import *


# ENHANCE: use API 'field' attribute to only return used fileds


# ENHANCE: searching for FIRSTNAME=Frederic LASTNAME=Fol Leymarie AFFIL=University of London, UK
# yeilds no results, although searching without UK yeilds the correct result
def find_author(author):
    score_threshold = 70
    query = f"AUTHFIRST({author.getattr('firstname')}) AND \
        AUTHLASTNAME({author.getattr('middlename')} {author.getattr('lastname')}) AND \
        AFFIL({author.getattr('affiliation')})"

    # Author(eid, surname, initials, givenname, affiliation, documents, affiliation_id, city, country, areas)
    possible_people = AuthorSearch(query).authors
    if not possible_people:
        return None

    aff_list = [f"{p.affiliation}, {p.country}" for p in possible_people]
    affiliation, fuzz_score = process.extractOne(author.affiliation, aff_list, scorer=fuzz.token_set_ratio)

    if fuzz_score > score_threshold or (len(aff_list) == 1 and fuzz_score == 0):
        author.eid_list = [p.eid for p in possible_people if affiliation.lower() == f"{p.affiliation}, {p.country}".lower()]
        return author
    elif len([a[0] for a in aff_list.items() if not len(a[1])]) > 1: 
        # "multiple_no_affiliation"
        # ENHANCE: handle no affiliation and wrong affiliation
        return None
    else: 
        # "wrong_affiliation"
        return None


# ENHANCE: filtrare i risultati tramite levenshtein, vedere se sono conference o journals (quindi vol. o anno) e vedere se l'anno va bene come filtro
def find_conference_papers(conference):
    query = f"SRCTITLE({conference.getattr('name')}) AND PUBYEAR = {conference.getattr('year')}"

    documents = ScopusSearch(query, view="STANDARD")
    conference.papers = [Paper(sid) for sid in documents.get_eids()]


# FIXME: implement references view
def extract_references_from_paper(paper):
    references = AbstractRetrieval(paper.scopus_id, view="FULL", refresh=True).references
    paper.references = [Reference(r.id, r.authors) for r in references]




# # a = find_author(Person("Xiaodong Lin", firstname="Xiaodong", lastname="Lin", affiliation="University of Ontario Institute of Technology, Canada"))
# # a = find_conference_papers(Conference('Journal of Computer Security, 2015', 'Journal of Computer Security', '2015'))
# a = extract_references_from_paper(Paper('2-s2.0-84951753303'))
# print(a)

# program_committee = list()
# conference = Conference()

# # program committee extraction
# for author in program_committee:
#     author = find_author(author)

# # conference papers extraction
# conference_papers = find_conference_papers(conference)
# # conference papers' references extraction
# for paper in conference_papers:
#     paper = extract_references_from_paper(paper)

# # check if conference papers have references to a member of a program committee
# for paper in conference_papers:
#     for reference in paper.references:
#         # TODO: usare un RDBMS per storare le info
#     for author in program_committee:
#         # se l'autore ha una paper tra le reference campo autore ++
#         # num. volte citato ++
#         # num conferenze in cui e' membro ++