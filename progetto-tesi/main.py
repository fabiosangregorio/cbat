from multiprocessing import Pool
import time

from bs4 import BeautifulSoup

import webutil
import dblp
import wiki_cfp
import elsevier
import program_extractor
from models import Author, Paper, Conference 
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
            wikicfp_id='10040',
            fullname="SMVC 2010 : ACM Multimedia Workshop on Surreal Media and Virtual Cloning 2010",
            name="ACM Multimedia Workshop on Surreal Media and Virtual Cloning",
            year="2010"
        )
    else:
        return Conference(
            wikicfp_url=conf_url,
            wikicfp_id='52345',
            fullname="SecureComm 2016 : 12th EAI International Conference on Security and Privacy in Communication Networks",
            name="SecureComm",
            year="2016"
        )


def add_conferences(conferences_urls, nlp):
    added_conferences = list()
    i = 0
    for conf_url in conferences_urls:
        conf = get_conference(conf_url)
        if Conference.objects(wikicfp_id=conf.wikicfp_id):
            return

        cfp = wiki_cfp.get_cfp(conf.wikicfp_url)

        # program_committee = program_extractor.extract_program_committee(cfp, nlp)
        program_committee = load_program_committee(i)
        i += 1 # HACK: remove when switching back to NER

        # save program committee to db
        authors = list()
        for p in program_committee:
            author = elsevier.find_author(p)
            if author == None:
                continue
            db_author = Author.objects(eid_list__in=author.eid_list).first()

            # FIXME: not an atomic operation, could result in problems with multithreading
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
        for paper in conf.papers:
            ref_eids = elsevier.extract_references_from_paper(paper)
            # tre alternative:
            # 1. mi salvo in Author anche gli autori non di commissione
            #    e nelle references metto tutti (ce bisogno di un campo che 
            #    dice che l'autore era in una commisssione, oppure si vede
            #    dal fatto che non e' figlio di nessun conference.program_committee)
            # 2. non mi salvo gli autori NON di commissione. nelle reference
            #    allora metto solo gli eid? oppure metto una lista di eid e 
            #    una lista di objid per i membri della conference citati
            # in effetti non mi interessano gli autori non di prog_com., pero
            # mi servono per dire prob non com di essere citato / prob com di
            # essere citato, e prob non com e' num cit dell'autore/tot citazioni
            # 3. salvare l'author e salvare le references in due campi:
            #    ref_prog_com e ref_NON_prog_com e tot_ref cosi' posso fare
            #    non cit autore = for conf for paper paper.ref_non_com
            # Scelgo 3.
            for eid in ref_eids:
                auth = next((a for a in conf.program_committee 
                            if eid in a.eid_list), None)
                if auth:
                    paper.program_refs.append(auth)
                    continue

                auth = Author.objects(eid_list__in=[eid]).first()
                if not auth:
                    auth = Author(eid_list=[eid]).save()
                paper.non_program_refs.append(auth)
                
            paper.save()
            

    return added_conferences


if __name__ == "__main__":
    # conferences_urls = ["http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040",
                        #   "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345"]
    conferences_urls = ["http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345"]
    # start_time = time.time()
    # nlp = spacy.load('en_core_web_md')
    # print('Loading NER: ', time.time() - start_time)

    # added_conferences = add_conferences(conferences_urls, nlp)
    added_conferences = add_conferences(conferences_urls, None)

    # TODO: compare references with program committee
    

# # check if conference papers have references to a member of a program committee
# for paper in conference_papers:
#     for reference in paper.references:
#     for author in program_committee:
#         # se l'autore ha una paper tra le reference campo autore ++
#         # num. volte citato ++
#         # num conferenze in cui e' membro ++
