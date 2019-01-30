import sys
import time
import urllib

from bs4 import BeautifulSoup

from fuzzywuzzy import process
from fuzzywuzzy import fuzz

import webutil


# gets the whole CFP from wikiCFP
def get_wikiCFP(url):
    start_time = time.time()

    response = webutil.get_page(url)
    html = BeautifulSoup(response["html"], 'html.parser')

    print('Download of paper: ', time.time() - start_time)
    return webutil.polish_html("".join([tag.getText() for tag in html.select('table .cfp')]))


def search_dblp(person):
    start_time = time.time()

    base_url = "https://dblp.org/search"
    query = urllib.parse.urlencode({"q": person.name})
    response = webutil.get_page(base_url + '/author?' + query)
    # request at /author gets redirected if the author is an exact match on the url. 
    # To be sure about it being the right one, we want to make it go through the same process as the other authors
    if response["redirected"]:
        response = webutil.get_page(base_url + '?' + query)

    html = BeautifulSoup(response["html"], 'html.parser')

    is_exact = html.select("#completesearch-authors > .body p")[0].getText().lower() == "exact matches"

    # first ul, either contains the exact matches or likely matches
    search_results = list()
    for li in html.select("#completesearch-authors > .body ul")[0].select('li'):
        search_results.append(Person( 
            name="".join([m.getText() for m in li.select('a mark')]),
            affiliation=li.select('small')[0].getText() if li.select('small') else "",
            dblp_url=li.select('a')[0]['href']
        ))
    # TODO: esportare la ricerca dell'affiliazione in un'altra funzione in modo da rendere modulare il tutto, in modo da poter dare in pasto dati di vari siti
    # TODO: se il token_set_ratio va sotto una certa soglia, aprire le prime n *da capire quante* pagine finche non si trova un'affiliazione precedente con token_set_ratio

    print('Search of name in dblp: ', time.time() - start_time)
    return {
        "name": "token_set_ratio", 
        "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.token_set_ratio, limit=20)
    }



# def get_papers_from_dblp(url):
#     start_time = time.time()

#     response = get_page(url)
#     html = BeautifulSoup(response, 'html.parser')
#     publ_url = html.select('.export a[href*="https://dblp.org/pers/xx/a/"')[0]['href']
#     response = get_page(publ_url)

#     print('Search of papers in dblp: ', time.time() - start_time)
