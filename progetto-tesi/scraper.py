from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import sys
import os
import time
import urllib


# handles the request for a generic webpage
def get_page(url):
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if resp.status_code == 200 and content_type is not None and content_type.find('html') > -1:
                return resp.content
            else:
                return None
    except RequestException as e:
        print(f'Error during requests to {url} : {str(e)}')
        return None


# strips whitespaces and only gets lines with valuable text
def polish_html(html):
    html = html.replace('\r', '\n')
    html = os.linesep.join([s for s in html.splitlines() if len(s.strip()) >= 4])
    return html


# gets the CFP from wikiCFP
def get_wikiCFP(url):
    start_time = time.time()

    response = get_page(url)
    html = BeautifulSoup(response, 'html.parser')

    print('Download of paper: ', time.time() - start_time)
    return polish_html("".join([tag.getText() for tag in html.select('table .cfp')]))


def search_dblp(person):
    start_time = time.time()

    base_url = "https://dblp.org/search/author?"
    response = get_page(base_url + urllib.parse.urlencode({"q": person.name}))
    html = BeautifulSoup(response, 'html.parser')

    is_exact = html.select("#completesearch-authors > .body p:first-child")[0].getText().lower() == "exact matches"

    # first ul, either contains the exact matches or likely matches
    for li in html.select("#completesearch-authors > .body ul")[0].select('li'):
        result = { 
            name: " ".join(li.select('a mark').getText()),
            affiliation: li.select('small')[0].getText(),
            url: li.select('a')[0]['href']
        }
        # TODO: implementare la distanza di levestein per prendere l'affiliazione giusta
        # in poche parole devo ciclare su tutti gli li, vedere se il nome e' uguale e se l'affiliazione e' uguale, rispetto alla distanza

    
    print('Search of name in dblp: ', time.time() - start_time)
    return None


def get_papers_from_dblp(url):
    start_time = time.time()

    response = get_page(url)
    html = BeautifulSoup(response, 'html.parser')
    publ_url = html.select('.export a[href*="https://dblp.org/pers/xx/a/"')[0]['href']
    response = get_page(publ_url)

    print('Search of papers in dblp: ', time.time() - start_time)
