import re
from datetime import datetime

import xlrd
from fuzzywuzzy import fuzz
from scopus import AbstractRetrieval

import cfp_manager
import conference_manager
import committee_manager
import author_manager
import paper_manager
import util.webutil as webutil
from models import Conference, Author, Paper
from util.helpers import printl


base_url = 'http://www.wikicfp.com'


def load_from_xlsx(path):
    """Loads conference names from xlsx file"""
    workbook = xlrd.open_workbook(path, "rb")
    sheets = workbook.sheet_names()
    conferences = []
    for sheet_name in sheets:
        sh = workbook.sheet_by_name(sheet_name)
        for rownum in range(2, sh.nrows):
            row = sh.row_values(rownum)
            conferences.append(Conference(name=row[1], acronym=row[2]))
    return conferences


def search_conference(conf, lower_boundary=5, exclude_current_year=True):
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
    api_calls = 0

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
        print('Program committee not found. Skipping conference.')
        return None

    print('Program committee extraction: found {0}, {1} without affiliation.'
          .format(len(program_committee),
                  len([p for p in program_committee if len(p.affiliation) < 2])))

    # Find authors and save them to db
    authors, authors_not_found = author_manager.find_authors(program_committee)
    api_calls += 2 * len(authors) + authors_not_found
    authors_list = list()
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
            authors_list.append(db_author)
        else:
            author.save()
            authors_list.append(author)

    conf.program_committee = authors_list
    conf.processing_status = "committee_extracted"
    conf.save()

    print('Author extraction: extracted {0}. Total not extracted: {1}'
          .format(len(authors), authors_not_found))

    # save conference papers to db
    # IMPROVE: if no papers are found, remove the conference from db?
    # it could distort the statistics
    papers = paper_manager.get_papers(conf)

    api_calls += len(papers)

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

    # get conference's subject areas
    subject_areas = conference_manager.get_subject_areas(conf)
    api_calls += len(paper)
    conf.modify(set__subject_areas=subject_areas)

    printl('Getting references from papers')
    # save references to db
    ref_to_committee = 0
    ref_not_to_committee_db = 0
    ref_not_to_committee_not_db = 0
    for paper in conf.papers:
        ref_eids = paper_manager.extract_references_from_paper(paper)
        api_calls += len(paper)

        for eid in ref_eids:
            # if there's a reference to the program committee, get the pc author
            found = False
            for a in conf.program_committee:
                if eid in a.eid_list:
                    paper.committee_refs.append(a)
                    found = True
                    continue
            if found:
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
        printl('.')

    print(' Done')
    conf.processing_status = 'complete'
    conf.save()

    print(f'REFERENCES OF ALL PAPERS EXTRACTION: \nRefs to committee: '
          f'{ref_to_committee}, Refs not to committee already in db: '
          f'{ref_not_to_committee_db}, ref not to committee not in db: '
          f'{ref_not_to_committee_not_db}')

    print(api_calls)
