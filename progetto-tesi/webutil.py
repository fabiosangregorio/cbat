import os
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from logging import warning

from bs4 import BeautifulSoup

# handles the request for a generic webpage
def get_page(url):
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if (resp.status_code == 200 and content_type is not None and 
                content_type.find('html') > -1):
                return {
                    "html": BeautifulSoup(resp.content, 'html.parser'),
                    "redirected": len(resp.history) > 0
                }
            else:
                return {
                    "html": BeautifulSoup('', 'html.parser'),
                    "redirected": len(resp.history) > 0
                }
    except RequestException as e:
        warning(f'Error during requests to {url} : {str(e)}')
        return {
            "html": BeautifulSoup('', 'html.parser'),
            "redirected": False
        }


# strips whitespaces and only gets lines with valuable text
def polish_html(html):
    if not html:
        return None
        
    html = html.replace('\r', '\n')
    html = os.linesep.join([s for s in html.splitlines() if len(s.strip()) >= 4])
    return html