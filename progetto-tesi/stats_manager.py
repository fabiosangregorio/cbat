from collections import namedtuple

import matplotlib.pyplot as plt

from models import Paper, Conference


def plot_refs():
    data = list(Paper.objects.aggregate({
        '$project': {
            '_id': 0,
            'x': {'$add': [{'$size': "$committee_refs"}, {'$size': "$non_committee_refs"}]},
            'y': {'$size': "$committee_refs"}
        }
    }))
    x = [point['x'] for point in data]
    y = [point['y'] for point in data]
    plt.scatter(x, y)
    plt.show()


def get_author_stats(author):
    # Number of mentions from conferences in which author was in committee.
    committee_mentions = Paper.count(committee_refs__in=[author.id])
    # Number of conferences in which author was in committee.
    committee_confs = Conference.count(program_committee__in=[author.id])
    # Number of mentions from conferences in which author was not in committee.
    not_committee_mentions = Paper.count(non_committee_refs__in=[author.id])
    # Number of conferences in which author was not in committee.
    not_committee_confs = Paper.count() - committee_confs

    committee_mentions_ratio = committee_mentions / committee_confs
    not_committee_mentions_ratio = not_committee_mentions / not_committee_confs

    fields = 'committee_mentions_ratio not_committee_mentions_ratio'
    auth_stats = namedtuple('AuthorStats', fields)

    return auth_stats(committee_mentions_ratio, not_committee_mentions_ratio)
