import xlrd
import codecs

import elsevier
import wiki_cfp
from models import Conference, Author, Paper


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


def load_conferences_from_xlsx(path, col_idx=1, row_start_idx=2):
    workbook = xlrd.open_workbook(path, "rb")
    sheets = workbook.sheet_names()
    conf_names = []
    for sheet_name in sheets:
        sh = workbook.sheet_by_name(sheet_name)
        for rownum in range(row_start_idx, sh.nrows):
            row_valaues = sh.row_values(rownum)
            conf_names.append(row_valaues[col_idx])
    return conf_names


# TODO: implement get conference. Scopus Serach sucks, consider using dblp for 
# searching confererences, if Scopus fails. Conferences may be listed with a 
# different name, and papers of that conference may still exist on Scopus.
def get_conference(conf_name):
    # mi cerco ogni conferenza e mi prendo un po di anni
    # per vedere se posso trattare una conference il collo di bottiglia e' la 
    # disponibilita' dei membri del program committee, se non ho quelli
    # non posso fare niente.
    # quindi, se non disponibile su wiki cfp, andarle a pescare con crawling dai
    # siti delle conference
    # scopus fa

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


def add_conferences(conferences_names, nlp):
    added_conferences = list()
    i = 0
    for conf_name in conferences_names:
        conf = get_conference(conf_name)
        if Conference.objects(wikicfp_id=conf.wikicfp_id):
            return

        cfp = wiki_cfp.get_cfp(conf.wikicfp_url)

        # program_committee = program_extractor.extract_program_committee(cfp, nlp)
        program_committee = load_program_committee(i)
        i += 1  # HACK: remove when switching back to NER

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