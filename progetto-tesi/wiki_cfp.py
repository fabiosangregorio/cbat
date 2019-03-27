from collections import namedtuple

import time
from bs4 import BeautifulSoup

import webutil


# gets the whole CFP from wikiCFP
def get_cfp(url):
    response = webutil.get_page(url)
    html = BeautifulSoup(response["html"], 'html.parser')
    
    ext_sources = [a['href'] for a in html.select('.contsec tr:nth-child(3) a') 
        if '/cfp/' not in a['href']]
    external_source = ext_sources[0] if len(ext_sources) > 0 else None
    cfp_text = webutil.polish_html("".join(
        [tag.getText() for tag in html.select('table .cfp')]))
    cfp = namedtuple('Cfp', 'cfp_text external_source')
    return cfp(cfp_text, external_source)