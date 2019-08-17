from collections import namedtuple

import matplotlib.pyplot as plt
from scipy import polyfit
import numpy

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

    pl = polyfit(x, y, 1)

    plt.scatter(x, y)
    plt.plot(x, numpy.polyval(pl, x), 'r-')
    plt.title('Refs distribution in papers')
    plt.ylabel('Refs to program committee')
    plt.xlabel('Total refs')
    plt.show()
    print(numpy.corrcoef(x, y)[0, 1])


def get_author_stats(author):
    # Number of mentions from conferences in which author was in committee.
    committee_mentions = Paper.objects(committee_refs__in=[author.id]).count()
    # committee_confs = 0
    # conferences = Conference.objects(program_committee__in=[author.id])
    # for conf in conferences:
    #     if len(set(conf.subject_areas) ^ set(author.subject_areas)):
    #         committee_confs += 1

    # Number of conferences in which author was in committee.
    committee_confs = Conference.objects(program_committee__in=[author.id]).count()

    # Number of mentions from conferences in which author was not in committee.
    not_committee_mentions = Paper.objects(non_committee_refs__in=[author.id]).count()
    # Number of conferences in which author was not in committee.
    not_committee_confs = Conference.objects.count() - committee_confs

    committee_mentions_ratio = committee_mentions / committee_confs
    not_committee_mentions_ratio = not_committee_mentions / not_committee_confs

    fields = 'committee_ratio not_committee_ratio'
    auth_stats = namedtuple('AuthorStats', fields)

    return auth_stats(committee_mentions_ratio, not_committee_mentions_ratio)