from collections import namedtuple

import xlrd

import util.webutil as webutil


base_url = 'http://www.wikicfp.com'


# loads conference names from xlsx file
def load_from_xlsx(path):
    workbook = xlrd.open_workbook(path, "rb")
    sheets = workbook.sheet_names()
    conferences = []
    for sheet_name in sheets:
        sh = workbook.sheet_by_name(sheet_name)
        for rownum in range(2, sh.nrows):
            row = sh.row_values(rownum)
            conference = namedtuple('conference', 'name acronym')
            conferences.append(conference(name=row[1], acronym=row[2]))
    return conferences


# get conferences from wikicfp
def get_conferences(conf_name):
    url = f'{base_url}/cfp/servlet/tool.search?q={conf_name.acronym}&year=a'
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
        # to it's papers, therefore there's no point in having it in db.
        today = datetime.now().year
        if w_year >  today - 1 or w_year < today - CONF_YEAR_LB:
            continue

        w_url = base_url + first_row.select('a')[0]['href']
        w_name = first_row.select('td')[1].text
        w_acronym = w_acr_year[0]

        w_location = second_row.select('td')[1].text

        # use levenshtein to check if it's the right conference, based on the 
        # acronym OR the name
        if (fuzz.partial_ratio(conf_name.name.lower(), w_name.lower()) < 70 and 
            fuzz.token_set_ratio(conf_name.acronym.lower(), w_acronym.lower()) < 70):
            continue
        
        conferences.append(Conference(
            fullname=conf_name.name, name=conf_name.name, acronym=conf_name.acronym,
            location=w_location, year=w_year, wikicfp_url=w_url))

    return conferences