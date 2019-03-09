from multiprocessing import Pool
import time

from bs4 import BeautifulSoup

import webutil
import dblp
import wiki_cfp
import elsevier
import program_extractor
from models import *
from mongoengine import connect
import spacy


connect('tesi-triennale')


if __name__ == "__main__":
    # TODO: retrieve all conferences
    conferences_urls = ["http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040",
        "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345"]

    for conf_url in conferences_urls:
        conf = Conference(wikicfp_url=conf_url)
        cfp = wiki_cfp.get_cfp(conf.wikicfp_url)

        program_committee = program_extractor.extract_program_committee(cfp)
        authors_id = list()

        for author in program_committee:
            author = elsevier.find_author(author)
            saved_author = Author.objects(eid_list__nin=author.eid_list)
            if(saved_author):
                authors_id.append(saved_author.id)
            else:
                author.save()
                authors_id.append(author.id)


        #TODO: add program_committee to conference


    # html = dblp.get_wikiCFP(url)

    # program_committee = program_extractor.extract_program_committee(html)
    
    # with open('progetto-tesi/program_test.txt', 'r') as f:
    #     data = f.read()

    # program_committee = [Author(p.split('#')[0], p.split('#')[1]) for p in data.splitlines()]
    # people = list()

    # start_time = time.time()

    # with Pool(5) as p:
    #     people = p.map(dblp.find_author, program_committee)

    # print('Total search of name in dblp: ', time.time() - start_time)

