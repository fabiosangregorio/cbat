import xlrd
from collections import namedtuple
import codecs
from logging import info

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


def add_conferences(conferences, nlp):
    added_conferences = list()
    for conf in conferences:
        info(f'### BEGIN conference: {conf.acronym} {conf.year}')
        if Conference.objects(wikicfp_id=conf.wikicfp_id):
            return

        cfp = wikicfp.get_cfp(conf.wikicfp_url)
        program_committee = program_extractor.extract_program_committee(cfp, nlp)
        info(f'FINISHED EXTRACT_PROGRAM_COMMITTEE:\nfound: {len(program_committee)}, '\
             f' without affiliation: {len([p for p in program_committee if len(p.affiliation) < 2])}')
        # Having a conference without program committee means we can't compare
        # the references, therefore there's no point in having it saved to db.
        if not program_committee:
            info('Program committee not found')
            continue

        # save program committee to db
        authors = list()
        info('Authors not extracted:')
        extracted = 0
        not_extracted = 0
        for p in program_committee:
            author = elsevier.find_author(p)
            if author == None:
                not_extracted += 1
                continue
            db_author = Author.objects(eid_list__in=author.eid_list).first()

            # FIXME: not an atomic operation, could result in problems with multithreading
            if db_author:
                # merge the new and old eid list 
                db_eid = db_author.eid_list
                new_eid = author.eid_list
                db_author.eid_list = db_eid + list(set(new_eid) - set(db_eid))
                db_author.save()
                authors.append(db_author)
            else:
                author.save()
                authors.append(author)
            extracted += 1

        conf.program_committee = authors
        conf.processing_status = 'committee_extracted'
        conf.save()
        info(f'Total authors extracted: {extracted} Total not extracted: {not_extracted}')

        # save conference papers to db
        # IMPROVE: if no papers are found, remove the conference from db?
        # it could distort the statistics
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
        conf.processing_status = 'papers_extracted'
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
        
        conf.processing_status = 'complete'
        conf.save()

    return added_conferences