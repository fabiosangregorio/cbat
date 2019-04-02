import xlrd
from collections import namedtuple
import codecs

import elsevier
import wikicfp
import program_extractor
from models import Conference, Author, Paper


# loads conference names from xlsx file
def load_conferences_from_xlsx(path):
    workbook = xlrd.open_workbook(path, "rb")
    sheets = workbook.sheet_names()
    conferences = []
    for sheet_name in sheets:
        sh = workbook.sheet_by_name(sheet_name)
        for rownum in range(2, sh.nrows):
            row = sh.row_values(rownum)
            conference = namedtuple('conference', 'name acronym')
            conferences.append(conference(name=row[1],acronym=row[2]))
    return conferences


'''
    TODO: implement get conference. Scopus Serach sucks, consider using dblp for 
    searching confererences, if Scopus fails. Conferences may be listed with a 
    different name, and papers of that conference may still exist on Scopus.
    def get_conference(conf_name):

        get_conference:
        for each row of file get name and acronym.
        check which years of conference there are (with a program committee) in both 
        wikicfp and scopus. (? all of the years? how many?)
        search in wikicfp for acronym and get the years.
        search in scopus for acronym and get the years
        ! check if there is information of all the years available (just like in
          the filters) = no! but the bottleneck is wikicfp anyway. i just need to 
          check if there are papers for the wikicfp year on scopus.

        for each year:
            1. scopus
        search CONFNAME() and get papers of the current year. 
        search for acronym, its the best way. for each paper get the description 
        which contains the conf name and acronym and use levenshtein (with a 
        different token) to check if the conference is the right one.
            2. wikicfp
        search for acronym, parse years and navigate to the right year. get program
        committee. discard if there is no program committee.

        conferences = wikicfp.get_conferences(conf_name)


        return conf
        # if conf_name == "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040":
        #     return Conference(
        #         wikicfp_url=conf_name,
        #         wikicfp_id='10040',
        #         fullname="SMVC 2010 : ACM Multimedia Workshop on Surreal Media and Virtual Cloning 2010",
        #         name="ACM Multimedia Workshop on Surreal Media and Virtual Cloning",
        #         year="2010"
        #     )
        # else:
        #     return Conference(
        #         wikicfp_url=conf_name,
        #         wikicfp_id='52345',
        #         fullname="SecureComm 2016 : 12th EAI International Conference on Security and Privacy in Communication Networks",
        #         name="SecureComm",
        #         year="2016"
        #     )
        # if i == 0:
        #     return Conference(wikicfp_url="http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=28432&copyownerid=2")
        # if i == 1:
        #     return Conference(wikicfp_url="http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=77406&copyownerid=84748")
        # if i == 2:
        #     return Conference(wikicfp_url="http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=77833&copyownerid=101501")    
'''
def add_conferences(conferences, nlp):
    added_conferences = list()
    for conf in conferences:
        if Conference.objects(wikicfp_id=conf.wikicfp_id):
            return

        cfp = wikicfp.get_cfp(conf.wikicfp_url)
        program_committee = program_extractor.extract_program_committee(cfp, nlp)

        # Having a conference without program committee means we can't compare
        # the references, therefore there's no point in having it saved to db.
        if not program_committee:
            continue

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
        papers_found = elsevier.get_conference_papers(conf)
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