from mongoengine import connect
import spacy

import cbat.conference_manager as conference_manager
import cbat.stats_manager as stats_manager
from cbat.models import Conference, Author

from cbat.config import SPACY_MODEL, DB_NAME


def add_conferences(conferences):
    for conf in conferences:
        add_conference(conf)


def add_conference(conferece):
    connect(DB_NAME, host='localhost')
    conf_editions = conference_manager.search_conference(conferece)
    for edition in conf_editions:
        print(f'\n### BEGIN conference: {edition.acronym} {edition.year} ###')
        conference_manager.add_conference(edition, nlp)


def add_authors_stats(authors = None):
    if authors is None:
        authors = Author.objects() 
    for author in authors:
        stats = stats_manager.get_author_stats(author)
        author.modify(committee_mentions=stats.committee_ratio,
                      total_mentions=stats.not_committee_ratio)


def plot_refs():
    stats_manager.plot_refs()


nlp = spacy.load(SPACY_MODEL)

