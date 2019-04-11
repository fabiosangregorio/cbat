from collections import namedtuple
from fuzzywuzzy import fuzz
import re
from datetime import datetime

import time
from bs4 import BeautifulSoup

from models import Conference
from config import CONFERENCES_YEAR_LOWER_BOUNDARY as CONF_YEAR_LB

import webutil


base_url = 'http://www.wikicfp.com'

# gets the whole CFP from wikiCFP, as well as the external url of the conference
def get_cfp(url):
    html = webutil.get_page(url)['html']
    if not html.text:
        return None
    
    ext_sources = [a['href'] for a in html.select('.contsec tr:nth-child(3) a') 
        if '/cfp/' not in a['href']]
    external_source = ext_sources[0] if (len(ext_sources) > 0 and 
        'mailto:' not in ext_sources[0]) else None
    cfp_text = webutil.polish_html("".join(
        [tag.getText() for tag in html.select('table .cfp')]))
    cfp = namedtuple('Cfp', 'cfp_text external_source')
    return cfp(cfp_text, external_source)


# get conferences from wikicfp
def get_conferences(conf_name):
    url = f'{base_url}/cfp/servlet/tool.search?q={conf_name.acronym}&year=a'
    html = webutil.get_page(url)['html']
    if not html.text:
        return None

    rows = html.select('.contsec table table tr')
    events = [[i, k] for i,k in zip(rows[1::2], rows[2::2])]
    
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

