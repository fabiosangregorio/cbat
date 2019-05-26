import re
from datetime import datetime

import xlrd
from fuzzywuzzy import fuzz
from scopus import AbstractRetrieval

import util.webutil as webutil
from models import Conference


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
    print("Getting conference subject areas", end="", flush=True)
    for paper in conference.papers:
        # FIXME: remove refresh=True when the following issue is resolved:
        # https://github.com/scopus-api/scopus/issues/99
        paper = AbstractRetrieval(paper.scopus_id, view="FULL", refresh=True)
        subject_areas += [s.code for s in paper.subject_areas]
        print(".", end="", flush=True)

    return list(set(subject_areas))
