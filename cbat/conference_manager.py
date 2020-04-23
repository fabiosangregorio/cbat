import re
from datetime import datetime
from multiprocessing import Pool, Lock
from mongoengine import connect

from fuzzywuzzy import fuzz
from pybliometrics.scopus import AbstractRetrieval

from cbat.config import WIKICFP_BASE_URL,  DB_NAME, CONF_EDITIONS_LOWER_BOUNDARY, MIN_COMMITTEE_SIZE, CONF_EXCLUDE_CURR_YEAR, AUTH_NO_AFFILIATION_RATIO

import cbat.cfp_manager as cfp_manager
import cbat.committee_manager as committee_manager
import cbat.author_manager as author_manager
import cbat.paper_manager as paper_manager
import cbat.util.webutil as webutil
from cbat.models import Conference, Author, Paper, AuthorIndex
from cbat.util.helpers import printl


base_url = WIKICFP_BASE_URL


def search_conference(conf, lower_boundary=CONF_EDITIONS_LOWER_BOUNDARY, exclude_current_year=CONF_EXCLUDE_CURR_YEAR):
    """
    Gets the conference editions from wikicfp.

    Args:
        lower_boundary: how many years in the past to search, expressed as an
            integer from the current year
        exclude_current_year: if True the results won't inlcude the conference
            edition of the current year (if present)

    Returns:
        A list of Conference objects representing all editions
    """
    url = f'{base_url}/cfp/servlet/tool.search?q={conf.acronym}&year=a'
    html = webutil.get_page(url)['html']
    if not html.text:
        return None

    rows = html.select('.contsec table table tr')
    events = [[i, k] for i, k in zip(rows[1::2], rows[2::2])]

    conferences = list()
    for event in events:
        first_row = event[0]
        second_row = event[1]
        w_acr_year = re.split(r'(\d+)(?!.)', first_row.select('a')[0].text)
        w_year = int(w_acr_year[1])

        # if the conference has not taken place yet, there can't be references
        # to its papers, therefore there's no point in having it in db.
        current_year = datetime.now().year
        if (w_year > current_year - exclude_current_year or
           w_year < current_year - lower_boundary):
            continue

        w_url = base_url + first_row.select('a')[0]['href']
        w_name = first_row.select('td')[1].text
        w_acronym = w_acr_year[0]
        w_location = second_row.select('td')[1].text

        # use levenshtein to check if it's the right conference, based on the
        # acronym OR the name
        if (fuzz.partial_ratio(conf.name.lower(), w_name.lower()) < 70 and
           fuzz.token_set_ratio(conf.acronym.lower(), w_acronym.lower()) < 70):
            continue

        conferences.append(Conference(
            fullname=conf.name, name=conf.name, acronym=conf.acronym,
            location=w_location, year=w_year, wikicfp_url=w_url))

    return conferences


def get_subject_areas(conference):
    subject_areas = []
    printl("Getting conference subject areas")
    for paper in conference.papers:
        paper = AbstractRetrieval(paper.scopus_id, view="FULL")
        subject_areas += [s.code for s in paper.subject_areas]
        printl(".")

    printl(" Done")
    return list(set(subject_areas))


def add_conference(conf, nlp):
    if Conference.objects(wikicfp_id=conf.wikicfp_id):
        print("Conference already in database. Skipping conference.")
        return

    # Get cfp and extract program committee
    cfp = cfp_manager.get_cfp(conf.wikicfp_url)
    printl('Extracting program committee ')
    program_sections = committee_manager.extract_program_sections(cfp.text)
    program_committee = committee_manager.extract_committee(program_sections, nlp)
    if not program_committee:
        cfp_text = cfp_manager.search_external_cfp(cfp.external_source)
        program_sections = committee_manager.extract_program_sections(cfp_text)
        program_committee = committee_manager.extract_committee(program_sections, nlp)
    if not program_committee:
        # Having a conference without program committee means we can't compare
        # the references, therefore there's no point in having it saved to db.
        print('Program committee not found. Skipping conference.')
        return None
    print(' Done')

    if len(program_committee) < MIN_COMMITTEE_SIZE:
        return

    n_no_aff = len([p for p in program_committee if len(p.affiliation) < 2])
    print('Program committee extraction: found {0}, {1} without affiliation.'
          .format(len(program_committee), n_no_aff))

    if n_no_aff / len(program_committee) > AUTH_NO_AFFILIATION_RATIO:
        return

    # Find authors and save them to db
    authors, authors_not_found = author_manager.find_authors(program_committee)
    authors_list = list()
    for author in authors:
        db_author = AuthorIndex.objects(eid__in=author.eid_list).first()
        if db_author:
            # FIXME: not an atomic operation, could result in problems with
            # multithreading
            db_author = db_author.author
            db_eid = db_author.eid_list
            new_eid = author.eid_list
            unique_new_eids = list(set(new_eid) - set(db_eid))
            merged_list = db_eid + unique_new_eids

            # Could be that an author is found as a references and added to the
            # db. Then this author is found to be a member of a program
            # committee. If I simply merge the EIDs, I will be missing out on
            # the newfound info on name, affiliation, etc.
            # Therefore, I just overwrite the info.
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

            for eid in unique_new_eids:
                AuthorIndex.objects.update(set_on_insert__eid=eid,
                                           set__author=db_author,
                                           upsert=True)

            authors_list.append(db_author)
        else:
            author.save()
            AuthorIndex.objects.insert(
                [AuthorIndex(eid=eid, author=author) for eid in author.eid_list])
            authors_list.append(author)

    if not authors:
        print("Authors not found. Skipping conference.")
        return

    conf.program_committee = authors_list
    conf.processing_status = "committee_extracted"
    conf.save()

    print('Author extraction: extracted {0}. Total not extracted: {1}'
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

    print(f'Papers extraction: extracted {len(papers)} papers. '
          f'Papers already in db: {papers_already_in_db}')

    # # get conference's subject areas
    # subject_areas = conference_manager.get_subject_areas(conf)
    # conf.modify(set__subject_areas=subject_areas)

    printl('Getting references from papers')
    # save references to db
    pool = Pool()
    pool.map(_save_paper_refs, [(p, conf) for p in papers_to_add])
    pool.close()

    print(' Done')
    conf.processing_status = 'complete'
    conf.save()


index_lock = Lock()


def _save_paper_refs(data):
    connect(DB_NAME, host='localhost')
    global index_lock
    paper, conf = data
    ref_eids = paper_manager.extract_references_from_paper(paper)
    for eid in ref_eids:
        # if there's a reference to the program committee, get the pc author
        found = False
        for a in conf.program_committee:
            if eid in a.eid_list:
                paper.committee_refs.append(a)
                found = True
                break
        if found:
            continue
        # else:
        #     auth = Author.objects(eid_list__in=eid).upsert_one(
        #         set_on_insert__eid_list=[eid])
        # FIXME: check why upsert is not working
        index_lock.acquire()
        auth = AuthorIndex.objects(eid=eid).first()
        # auth = Author.objects(eid_list__in=[eid]).first()
        if auth:
            auth = auth.author
        else:
            auth = Author(eid_list=[eid]).save()
            AuthorIndex(eid=eid, author=auth).save()
        index_lock.release()

        paper.non_committee_refs.append(auth)

    if not ref_eids:
        printl('x')
        paper.delete()
        return

    paper.save()
    printl('.')
 