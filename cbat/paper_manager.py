from pybliometrics.scopus import AbstractRetrieval, ScopusSearch

from cbat.models import Paper


# IMPROVE: use API 'field' attribute to only return used fileds


def get_papers(conference):
    # IMPROVE: filtrare i risultati tramite levenshtein, vedere se sono conference
    # o journals (quindi vol. o anno) e vedere se l'anno va bene come filtro
    # IMPROVE: non tutte le conferences sono listate in scopus, ma possono avere
    # le paper. es: https://dblp.org/db/conf/securecomm/securecomm2016.html
    # quindi cercare anche su dblp le conference e cercare le paper su scopus
    # TODO: refactor this method using the conference info from CONFNAME
    query = f"SRCTITLE({conference.getattr('acronym')}) \
              AND PUBYEAR = {conference.getattr('year')}"

    documents = ScopusSearch(query, view="STANDARD")
    try:
        papers = [Paper(scopus_id=sid) for sid in documents.get_eids()]
    except Exception:
        return []

    return papers


def extract_references_from_paper(paper):
    # IMPROVE: many retrievals fail
    try:
        references = AbstractRetrieval(paper.scopus_id, view="REF").references
    except Exception:
        return []

    if not references:
        return []

    eids = [int(auid.strip()) for ref in references if ref.authors_auid
            for auid in ref.authors_auid.split('; ')]
    return eids
