from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import sys
import os
import time


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


def get_CFP(url):
    start_time = time.time()

    response = get_page(url)

    if response is None:
        raise Exception(f'Error retrieving contents at {url}')

    html = BeautifulSoup(response, 'html.parser')

    print('Download of paper: ', time.time() - start_time)
    return polish_html("".join([tag.getText() for tag in html.select('table .cfp')]))


def polish_html(html):
    html = html.replace('\r', '\n')
    # strips whitespaces and only gets lines with text
    html = os.linesep.join([s for s in html.splitlines() if len(s.strip()) >= 4])
    return html