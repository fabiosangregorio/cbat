import time
from bs4 import BeautifulSoup

import webutil


# gets the whole CFP from wikiCFP
def get_wikiCFP(url):
    start_time = time.time()

    response = webutil.get_page(url)
    html = BeautifulSoup(response["html"], 'html.parser')

    print('Download of paper: ', time.time() - start_time)
    return webutil.polish_html("".join([tag.getText() for tag in html.select('table .cfp')]))