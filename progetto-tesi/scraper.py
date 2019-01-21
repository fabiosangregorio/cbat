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


def search_dblp(name):
    start_time = time.time()

    base_url = "https://dblp.org/search?"
    response = get_page(base_url + urllib.parse.urlencode({"q": name}))
    html = BeautifulSoup(response, 'html.parser')
    name_urls = html.select("#completesearch-authors > .body ul a")
    
    if(html.select("#completesearch-authors > .body p")[0].getText().lower() == "exact matches"):
        exact_message = "exact"
    elif(len(name_urls) == 1 and not is_exact):
        exact_message = "only_likely"
    elif(len(name_urls) > 1):
        exact_message = "first_likely"
    else:
        exact_message = "none"
        name_urls = None 
    
    return { is_exact: exact_message, name_urls: name_urls[0] }

    print('Search of name in dblp: ', time.time() - start_time)

def get_papers_from_dblp(url):
    start_time = time.time()
