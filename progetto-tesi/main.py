#!/usr/bin/env python3
from multiprocessing import Pool
import time

from bs4 import BeautifulSoup
from mongoengine import connect
import spacy

import webutil
import dblp
import wiki_cfp
import elsevier
import program_extractor
from models import Author, Paper, Conference
import conferences


connect('tesi-triennale')


if __name__ == "__main__":
    # conferences_urls = ["http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040",
                        #   "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345"]
    start_time = time.time()
    nlp = spacy.load('en_core_web_sm')
    print('Loading NER: ', time.time() - start_time)

    # added_conferences = add_conferences(conferences_urls, nlp)
    # added_conferences = add_conferences(conferences_urls, None)
    conf_names = conferences.load_conferences_from_xlsx("./progetto-tesi/cini.xlsx")[0:3]
    added_conferences = conferences.add_conferences(conf_names, nlp)

    # TODO: compare references with program committee


# # check if conference papers have references to a member of a program committee
# for paper in conference_papers:
#     for reference in paper.references:
#     for author in program_committee:
#         # se l'autore ha una paper tra le reference campo autore ++
#         # num. volte citato ++
#         # num conferenze in cui e' membro ++
