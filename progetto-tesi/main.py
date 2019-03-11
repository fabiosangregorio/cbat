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


def add_conferences(conferences_urls):
    added_conferences = list()
    for conf_url in conferences_urls:
        conf = Conference(wikicfp_url=conf_url)
        cfp = wiki_cfp.get_cfp(conf.wikicfp_url)
        program_committee = program_extractor.extract_program_committee(cfp)

        # save program committee to db
        authors = list()
        for p in program_committee:
            author = elsevier.find_author(p)
            if author == None:
                continue
            db_author = Author.objects(eid_list__in=author.eid_list).first()
            if db_author:
                authors.append(db_author)
            else:
                author.save()
                authors.append(author)

        conf.program_committee = authors
        conf.save()

        # save conference papers to db
        papers_found = elsevier.find_conference_papers(conf)
        papers = list()
        for paper in papers_found:
            db_paper = Paper.objects(scopus_id=paper.scopus_id).first()
            if db_paper:
                papers.append(db_paper)
            else:
                paper.save()
                papers.append(paper)

        conf.papers = papers
        conf.save()
        added_conferences.append(conf)
    
    return added_conferences


if __name__ == "__main__":
    # TODO: retrieve all conferences
    added_conferences = add_conferences([
        "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040",
        "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345"])


    for conf in added_conferences:
        for paper in conf.papers:
            references = elsevier.extract_references_from_paper(paper)
            paper.references = Author.objects(eid_list__in=references)
            paper.save()


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

