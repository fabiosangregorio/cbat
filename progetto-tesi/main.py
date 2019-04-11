import logging
from logging import info

from mongoengine import connect

import cfp_manager
import committee_manager
import author_manager

from .models import Conference, Author, Paper


logging.basicConfig(level=logging.INFO)
connect('tesi-triennale')


def _add_conference(conf, nlp):
    if Conference.objects(wikicfp_id=conf.wikicfp_id):
        return

    # Get cfp and extract program committee
    cfp = cfp_manager.get_cfp(conf.wikicfp_url)
    program_sections = committee_manager.extract_program_sections(cfp.text)
    if len(program_sections) == 0:
        cfp = cfp_manager.search_external_cfp(cfp.external_source)
        program_sections = committee_manager.extract_program_sections(cfp.text)
    program_committee = committee_manager.extract_committee(cfp, nlp)

    if not program_committee:
        # Having a conference without program committee means we can't compare
        # the references, therefore there's no point in having it saved to db.
        info('Program committee not found')
        return None

    info('PROGRAM COMMITTEE EXTRACTION:\nFound: {0}, Without affiliation: {1}'
         .format(len(program_committee),
                 len([p for p in program_committee if len(p.affiliation) < 2])))

    # save program committee to db
    authors = list()
    for p in program_committee:
        author = author_manager.find_author(p)
        if author is None:
            authors.append(None)
            continue

        db_author = Author.objects(eid_list__in=author.eid_list).first()
        # FIXME: not an atomic operation, could result in problems with
        # multithreading
        if db_author:
            # merge the new and old eid list
            db_eid = db_author.eid_list
            new_eid = author.eid_list
            merged_list = db_eid + list(set(new_eid) - set(db_eid))
            '''
            Could be that an author is found as a references and added to the
            db. Then this author is found to be a member of a program committee.
            If I simply merge the EIDs, I will be missing out on the newfound
            info on name, affiliation, etc. Therefore, I just overwrite the infos.
            '''
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
            authors.append(db_author)
        else:
            author.save()
            authors.append(author)

    conf.program_committee = authors
    conf.processing_status = 'committee_extracted'
    conf.save()

    info(f'AUTHORS EXTRACTION: \nTotal authors extracted: {extracted} '\
        f'Total not extracted: {not_extracted}')

    # save conference papers to db
    # IMPROVE: if no papers are found, remove the conference from db?
    # it could distort the statistics
    papers_found = elsevier.get_conference_papers(conf)
    papers = list()
    papers_already_in_db = 0
    for paper in papers_found:
        db_paper = Paper.objects(scopus_id=paper.scopus_id).first()
        if db_paper:
            papers.append(db_paper)
            papers_already_in_db += 1
        else:
            paper.save()
            papers.append(paper)

    conf.modify(set__papers=papers, 
                set__processing_status='papers_extracted')

    info(f'PAPERS EXTRACTION: \nTotal papers extracted: {len(papers)}, '\
        f'Papers already in db: {papers_already_in_db}')
    
    # save references to db
    ref_to_committee=0
    ref_not_to_committee_db=0
    ref_not_to_committee_not_db=0
    for paper in conf.papers:
        ref_eids = elsevier.extract_references_from_paper(paper)  
        for eid in ref_eids:
            auth = next((a for a in conf.program_committee
                            if eid in a.eid_list), None)
            if auth:
                paper.committee_refs.append(auth)
                continue
            # else:
            #     auth = Author.objects(eid_list__in=eid).upsert_one(
            #         set_on_insert__eid_list=[eid])

            auth = Author.objects(eid_list__in=[eid]).first()
            if not auth:
                auth = Author(eid_list=[eid]).save()
                ref_not_to_committee_not_db += 1
            else:
                ref_not_to_committee_db += 1

            paper.non_committee_refs.append(auth)
            
        ref_to_committee += len(paper.committee_refs)
        paper.save()
    
    conf.processing_status = 'complete'
    conf.save()

    info(f'REFERENCES OF ALL PAPERS EXTRACTION: \nRefs to committee: '\
        f'{ref_to_committee}, Refs not to committee already in db: '\
        f'{ref_not_to_committee_db}, ref not to committee not in db: {ref_not_to_committee_not_db}')


if __name__ == "__main__":
    start_time = time.time()
    nlp = spacy.load('en_core_web_sm')
    info(f'Loading NER: {time.time() - start_time}')

    conf_names = conferences.load_conferences_from_xlsx("./progetto-tesi/cini.xlsx")[0:1]
    for conf_name in conf_names:
        conf_editions = wikicfp.get_conferences(conf_name)
        conf_editions = [conf_editions[3]]
        for edition in conf_editions:
            info(f'##### BEGIN conference: {conf.acronym} {conf.year} #####')
            added_conferences = _add_conference(conf_editions, nlp)
