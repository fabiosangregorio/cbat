import os
from requests import get
from requests.exceptions import RequestException
from contextlib import closing


# handles the request for a generic webpage
def get_page(url):
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if resp.status_code == 200 and content_type is not None and content_type.find('html') > -1:
                return {
                    "html": resp.content,
                    "redirected": len(resp.history) > 0
                }
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