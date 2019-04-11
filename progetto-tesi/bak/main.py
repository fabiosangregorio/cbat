#!/usr/bin/env python3
from multiprocessing import Pool
import time
import logging
from logging import info

from bs4 import BeautifulSoup
from mongoengine import connect
import spacy

import webutil
import dblp
import wikicfp
import elsevier
import program_extractor
from models import Author, Paper, Conference
import conferences

logging.basicConfig(level=logging.INFO)
connect('tesi-triennale')


if __name__ == "__main__":
    start_time = time.time()
    nlp = spacy.load('en_core_web_sm')
    info(f'Loading NER: {time.time() - start_time}')

    conf_names = conferences.load_conferences_from_xlsx("./progetto-tesi/cini.xlsx")[0:1]
    for conf_name in conf_names:
        conf_editions = wikicfp.get_conferences(conf_name)
        conf_editions = [conf_editions[3]]
        added_conferences = conferences.add_conferences(conf_editions, nlp)

    # TODO: compare references with program committee


# # check if conference papers have references to a member of a program committee
# for paper in conference_papers:
#     for reference in paper.references:
#     for author in program_committee:
#         # se l'autore ha una paper tra le reference campo autore ++
#         # num. volte citato ++
#         # num conferenze in cui e' membro ++
