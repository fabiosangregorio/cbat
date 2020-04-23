from collections import namedtuple

import matplotlib.pyplot as plt
from scipy import polyfit
import numpy

from cbat.models import Paper, Conference


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

    plt.figure(1)
    plt.scatter(x, y, s=5)
    plt.xticks(numpy.arange(min(x), max(x)+1, 50.0))
    plt.yticks(numpy.arange(min(y), max(y)+1, 5.0))
    plt.ylabel('References to program committee')
    plt.xlabel('Total references')

    plt.figure(2)
    xx = range(0, len(x))
    yy = sorted(numpy.divide(y, x), reverse=True)
    plt.scatter(xx, yy, s=3)
    plt.xticks(numpy.arange(min(xx), max(xx)+1, 250.0))
    plt.yticks(numpy.arange(min(yy), max(yy)+1, 0.05))
    plt.ylabel('References to program committee / Total references ratio')
    plt.xlabel('Papers (sorted by ratio)')

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
    # committee_confs = Conference.objects(program_committee__in=[author.id]).count()

    # Number of mentions from conferences in which author was not in committee.
    not_committee_mentions = Paper.objects(non_committee_refs__in=[author.id]).count()
    # Number of conferences in which author was not in committee.
    # not_committee_confs = Conference.objects.count() - committee_confs

    # committee_mentions_ratio = committee_mentions / committee_confs
    # not_committee_mentions_ratio = not_committee_mentions / not_committee_confs

    fields = 'committee_ratio not_committee_ratio'
    auth_stats = namedtuple('AuthorStats', fields)

    return auth_stats(committee_mentions, not_committee_mentions + committee_mentions)