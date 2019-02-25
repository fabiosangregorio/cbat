#!/usr/bin/env python3

from multiprocessing import Pool
import time

from bs4 import BeautifulSoup

import webutil

import dblp
import program_extractor
from author import Author

if __name__ == "__main__":
    # # url con due righe
    # # url = "http://www.wikicfp.com/c2fp/servlet/event.showcfp?eventid=10040&copyownerid=12184"

    # # url con una riga
    # url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345&copyownerid=75434"
    # html = dblp.get_wikiCFP(url)

    # program_committee = program_extractor.extract_program_committee(html)
    
    with open('progetto-tesi/program_test.txt', 'r') as f:
        data = f.read()

    program_committee = [Author(p.split('#')[0], p.split('#')[1]) for p in data.splitlines()]
    people = list()

    start_time = time.time()

    with Pool(5) as p:
        people = p.map(dblp.find_author, program_committee)

    print('Total search of name in dblp: ', time.time() - start_time)

