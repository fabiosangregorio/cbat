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

import codecs


connect('tesi-triennale')


def load_program_committee(i):
    authors = list()
    with codecs.open(f"./progetto-tesi/dump{i}.txt", 'r', 'utf-8-sig') as f:
        data = f.read()

    for line in data.split('\n'): 
        splitted = line.split('#')
        authors.append(Author(
            fullname=f"{splitted[0]} {splitted[1]}",
            firstname=splitted[0],
            lastname=splitted[1],
            affiliation=splitted[2]
        ))

    return authors


# TODO: implement get conference. Scopus Serach sucks, consider using dblp for searching confererences,
# based on the percentage of failed attempts at Scopus Search.
def get_conference(conf_url):
    if conf_url == "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040":
        return Conference(
            wikicfp_url=conf_url,
            fullname="SMVC 2010 : ACM Multimedia Workshop on Surreal Media and Virtual Cloning 2010",
            name="ACM Multimedia Workshop on Surreal Media and Virtual Cloning",
            year="2010"
        )
    else:
        return Conference(
            wikicfp_url=conf_url,
            fullname="SecureComm 2016 : 12th EAI International Conference on Security and Privacy in Communication Networks",
            name="SecureComm",
            year="2016"
        )


def add_conferences(conferences_urls):
    added_conferences = list()
    i = 0
    for conf_url in conferences_urls:
        conf = get_conference(conf_url)
        cfp = wiki_cfp.get_cfp(conf.wikicfp_url)

        program_committee = program_extractor.extract_program_committee(cfp)
        # program_committee = load_program_committee(i)
        i += 1 # HACK: remove when switching back to NER

        # save program committee to db
        authors = list()
        for p in program_committee:
            author = elsevier.find_author(p)
            if author == None:
                continue
            db_author = Author.objects(eid_list__in=author.eid_list).first()

            # IMPROVE: not an atomic operation, could result in problems with multithreading
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

        # save references to db
        # for conf in added_conferences:
        # for paper in conf.papers:
        #     references = elsevier.extract_references_from_paper(paper)
        #     paper.references = Author.objects(eid_list__in=references)
        #     paper.save()

    return added_conferences


if __name__ == "__main__":
    added_conferences = add_conferences([
        "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040",
        "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345"])

    # TODO: compare references with program committee
    


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

