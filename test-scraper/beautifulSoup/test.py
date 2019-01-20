from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import sys


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
    response = get_page(url)

    if response is None:
        raise Exception(f'Error retrieving contents at {url}')

    html = BeautifulSoup(response, 'html.parser')
    # return "".join([tag.getText() for tag in html.select('table .cfp')])
    with open('dump.txt', 'w') as f:
        f.write("".join([tag.getText() for tag in html.select('table .cfp')]))


get_CFP("http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345&copyownerid=75434")