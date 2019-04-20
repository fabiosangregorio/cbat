import logging
from logging import info
import time

from mongoengine import connect
import spacy

import cfp_manager
import conference_manager
import committee_manager
import author_manager
import paper_manager
from models import Conference, Author, Paper


logging.basicConfig(level=logging.INFO)
connect('tesi-triennale')


def _add_conference(conf, nlp):
    if Conference.objects(wikicfp_id=conf.wikicfp_id):
        return

    # Get cfp and extract program committee
    cfp = cfp_manager.get_cfp(conf.wikicfp_url)
    program_sections = committee_manager.extract_program_sections(cfp.text)
    if len(program_sections) == 0:
        cfp_text = cfp_manager.search_external_cfp(cfp.external_source)
        program_sections = committee_manager.extract_program_sections(cfp_text)
    program_committee = committee_manager.extract_committee(program_sections, nlp)
    if not program_committee:
        # Having a conference without program committee means we can't compare
        # the references, therefore there's no point in having it saved to db.
        info('Program committee not found')
        return None

    info('PROGRAM COMMITTEE EXTRACTION:\nFound: {0}, Without affiliation: {1}'
         .format(len(program_committee),
                 len([p for p in program_committee if len(p.affiliation) < 2])))

    # Find authors and save them to db
    authors, authors_not_found = author_manager.find_authors(program_committee)
    for author in authors:
        db_author = Author.objects(eid_list__in=[author.eid_list]).first()
        if db_author:
            # FIXME: not an atomic operation, could result in problems with
            # multithreading
            db_eid = db_author.eid_list
            new_eid = author.eid_list
            merged_list = db_eid + list(set(new_eid) - set(db_eid))
            # Could be that an author is found as a references and added to the
            # db. Then this author is found to be a member of a program
            # committee. If I simply merge the EIDs, I will be missing out on
            # the newfound info on name, affiliation, etc.
            # Therefore, I just overwrite the infos.
            # IMPROVE: overwrite only if field is null.
            # https://stackoverflow.com/questions/55615467/update-field-if-is-null-in-mongoengine
            db_author.modify(
                set__fullname=db_author.fullname,
                set__firstname=db_author.firstname,
                set__middlename=db_author.middlename,
                set__lastname=db_author.lastname,
                set__affiliation=db_author.affiliation,
                set__affiliation_country=db_author.affiliation_country,
                set__eid_list=merged_list)
        else:
            author.save()

    conf.program_committee = authors
    conf.processing_status = "committee_extracted"
    conf.save()

    info('AUTHORS EXTRACTION:\n'
         'Total authors extracted: {0} Total not extracted: {1}'
         .format(len(authors), authors_not_found))

    # save conference papers to db
    # IMPROVE: if no papers are found, remove the conference from db?
    # it could distort the statistics
    papers = paper_manager.get_papers(conf)
    papers_to_add = list()
    papers_already_in_db = 0
    for paper in papers:
        db_paper = Paper.objects(scopus_id=paper.scopus_id).first()
        if db_paper:
            papers_to_add.append(db_paper)
            papers_already_in_db += 1
        else:
            paper.save()
            papers_to_add.append(paper)

    conf.modify(set__papers=papers_to_add, 
                set__processing_status='papers_extracted')

    info(f'PAPERS EXTRACTION: \nTotal papers extracted: {len(papers)}, '
         f'Papers already in db: {papers_already_in_db}')

    # save references to db
    ref_to_committee = 0
    ref_not_to_committee_db = 0
    ref_not_to_committee_not_db = 0
    for paper in conf.papers:
        ref_eids = paper_manager.extract_references_from_paper(paper)
        for eid in ref_eids:
            # if there's a reference to the program committee, get the pc author
            for a in conf.program_committee:
                if eid in a.eid_list:
                    paper.committee_refs.append(a)
                    continue
            # else:
            #     auth = Author.objects(eid_list__in=eid).upsert_one(
            #         set_on_insert__eid_list=[eid])
            # FIXME: check why upsert is not working
            auth = Author.objects(eid_list__in=[eid]).first()
            if auth:
                ref_not_to_committee_db += 1
            else:
                auth = Author(eid_list=[eid]).save()
                ref_not_to_committee_not_db += 1

            paper.non_committee_refs.append(auth)

        ref_to_committee += len(paper.committee_refs)
        paper.save()

    conf.processing_status = 'complete'
    conf.save()

    info(f'REFERENCES OF ALL PAPERS EXTRACTION: \nRefs to committee: '
         f'{ref_to_committee}, Refs not to committee already in db: '
         f'{ref_not_to_committee_db}, ref not to committee not in db: '
         f'{ref_not_to_committee_not_db}')


if __name__ == "__main__":
    start_time = time.time()
    nlp = spacy.load('en_core_web_sm')
    info(f'Loading NER: {time.time() - start_time}')

    confs = conference_manager.load_from_xlsx("./progetto-tesi/data/cini.xlsx")[0:1]
    for conf in confs:
        conf_editions = conference_manager.search_conference(conf)
        conf_editions = [conf_editions[3]]
        for edition in conf_editions:
            info(f'### BEGIN conference: {edition.acronym} {edition.year} ###')
            _add_conference(edition, nlp)
