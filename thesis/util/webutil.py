from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from logging import warning

from bs4 import BeautifulSoup


def meta_redirect(content):
    """
    Checks for a meta redirect tag
    (ex. <meta content="0; url=https://www.sigsac.org/ccs/CCS2018/papers/" http-equiv="refresh"/>)
    """
    soup = BeautifulSoup(content, 'html.parser')

    result = soup.find(
        lambda tag: tag.name == "meta" and tag.get("http-equiv", "").lower() == "refresh")
    if result:
        wait, text = result["content"].split(";")
        if text.strip().lower().startswith("url="):
            url = text[5:]
            return url
    return None


def get_page(url, redirected=False):
    """Handles the request for a generic webpage"""
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if (resp.status_code == 200 and content_type is not None and
               content_type.find('html') > -1):
                if meta_redirect(resp.content):
                    return get_page(meta_redirect(resp.content), True)
                return {
                    "html": BeautifulSoup(resp.content, 'html.parser'),
                    "redirected": redirected or len(resp.history) > 0
                }
            else:
                return {
                    "html": BeautifulSoup('', 'html.parser'),
                    "redirected": redirected or len(resp.history) > 0
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
    html = html.replace('\t', ' ')
    html = html.replace('\xa0', ' ')
    html = "\n".join([s for s in html.splitlines() if len(s.strip()) >= 2])
    return html
