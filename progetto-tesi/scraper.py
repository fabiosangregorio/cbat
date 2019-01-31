import sys
import time
import urllib

from bs4 import BeautifulSoup

from fuzzywuzzy import process
from fuzzywuzzy import fuzz

from person import Person
import webutil

score_threshold = 70

# gets the whole CFP from wikiCFP
def get_wikiCFP(url):
    start_time = time.time()

    response = webutil.get_page(url)
    html = BeautifulSoup(response["html"], 'html.parser')

    print('Download of paper: ', time.time() - start_time)
    return webutil.polish_html("".join([tag.getText() for tag in html.select('table .cfp')]))


def search_dblp(person_to_find):
    start_time = time.time()

    base_url = "https://dblp.org/search"
    query = urllib.parse.urlencode({"q": person_to_find.name})
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
    results = find_right_person(person_to_find, search_results, is_exact)
    print('Search of name in dblp: ', time.time() - start_time)
    return results


def find_right_person(person_to_find, people_list, is_exact):
    result_message = {
        "status": "ok",
        "is_exact": is_exact
    }

    affiliations = {idx: r.affiliation for idx, r in enumerate(people_list)}
    if len([a[0] for a in affiliations.items() if not len(a[1])]) > 1:
        # more than one person with the same name, without affiliation. I can't be sure of which name is the right one.
        # TODO: gestire il caso likely_match
        return {
            "status": "error",
            "err": "multiple_no_affiliation",
            "is_exact": is_exact
        }

    _, score, best_index = process.extractOne(person_to_find.affiliation, affiliations, scorer=fuzz.token_set_ratio)
    
    if score > score_threshold or (len(affiliations) == 1 and score == 0):
        # regular best match or only one match (no affiliation)
        result_message["result"] = people_list[best_index]
    elif score <= score_threshold:
        # no matches with affiliation, could be either another affiliation or an AKA (another name)
        _, name_score, best_name_index = process.extractOne(person_to_find.name, affiliations, scorer=fuzz.token_set_ratio)
        if name_score > score_threshold:    
            result_message["result"] = people_list[best_name_index]
        else:
            # the affiliation field is not the same as author's, might be an author's former affiliation
            for i, person in enumerate(people_list):
                if is_previous_affiliation(person, person_to_find.affiliation):
                    break
            if i < len(people_list):
                result_message["result"] = people_list[i]
            else:
                return {
                    "status": "error",
                    "err": "wrong_affiliation",
                    "is_exact": is_exact
                }
    
    return result_message


def is_previous_affiliation(person, affiliation):
    response = webutil.get_page(person.dblp_url)
    html = BeautifulSoup(response["html"], 'html.parser')

    affiliations = [tag.getText() for tag in html.select('.profile [itemprop=name]')]
    if not len(affiliations):
        return False
    _, score = process.extractOne(affiliation, affiliations, scorer=fuzz.token_set_ratio)
    return score > score_threshold


    # def get_papers_from_dblp(url):
    #     start_time = time.time()

    #     response = get_page(url)
    #     html = BeautifulSoup(response, 'html.parser')
    #     publ_url = html.select('.export a[href*="https://dblp.org/pers/xx/a/"')[0]['href']
    #     response = get_page(publ_url)

    #     print('Search of papers in dblp: ', time.time() - start_time)
