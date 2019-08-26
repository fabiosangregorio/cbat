from mongoengine import connect
import spacy

import conference_manager
import stats_manager
from models import Conference

from config import SPACY_MODEL, DB_NAME


def _add_conferences():
    nlp = spacy.load(SPACY_MODEL)

    confs = conference_manager.load_from_xlsx("./cbat/data/cini.xlsx")[88:100]
    for conf in confs:
        conf_editions = conference_manager.search_conference(conf)
        for edition in conf_editions:
            print(f'\n### BEGIN conference: {edition.acronym} {edition.year} ###')
            conference_manager.add_conference(edition, nlp)


def _add_authors_stats():
    authors = Conference.objects.distinct('program_committee')
    for author in authors:
        stats = stats_manager.get_author_stats(author)
        author.modify(committee_mentions_ratio=stats.committee_ratio,
                      not_committee_mentions_ratio=stats.not_committee_ratio)


connect(DB_NAME)
if __name__ == "__main__":
    # _add_conferences()
    stats_manager.plot_refs()
    # _add_authors_stats()
