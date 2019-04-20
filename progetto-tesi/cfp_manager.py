import requests
from collections import namedtuple
import re

import util.webutil as webutil
from config import HEADINGS, P_PROGRAM_HEADINGS


def get_cfp(url):
    """
    Gets the whole CFP from wikiCFP, as well as the external url of the conference.
    """
    html = webutil.get_page(url)['html']
    if not html.text:
        return None

    ext_sources = [a['href'] for a in html.select('.contsec tr:nth-child(3) a')
                   if '/cfp/' not in a['href']]
    external_source = None
    if len(ext_sources) > 0 and 'mailto:' not in ext_sources[0]:
        external_source = ext_sources[0]
    cfp_text = webutil.polish_html("".join(
        [tag.getText() for tag in html.select('table .cfp')]))
    cfp = namedtuple('Cfp', 'text external_source')
    return cfp(cfp_text, external_source)


def search_external_cfp(url, secondary=False):
    if not url:
        return None

    html = webutil.get_page(url)['html']
    if not html.text:
        return None
    if not secondary:
        # if a link to the conference's program committee is present, extract the
        # committee from there, otherwise extract it from the main external page.
        program_links = [tag for tag in html('a')
                         if any(h in tag.text.lower() for h in HEADINGS)]
        if len(program_links):
            link = None
            for l in program_links:
                if any(p in l.text.lower() for p in P_PROGRAM_HEADINGS):
                    # if there's a link with the words "program committee" take
                    # that one, otherwise just "committee" is ok
                    link = l
                    break
            if not link:
                link = program_links[0]
            full_url = requests.compat.urljoin(url, link['href'])
            return search_external_cfp(full_url, secondary=True)

    regex = re.compile('.*(' + '|'.join(P_PROGRAM_HEADINGS) + ').*', re.IGNORECASE)
    # tag.parent gets the tag
    program_tags = [tag.parent for tag in html.body(text=regex)]

    cfp_text = ""
    for tag in program_tags:
        # get unique parents of the tags (if several tags have the same parent,
        # keep only one)
        parent = tag.parent
        if any(t in parent for t in program_tags if t != tag):
            continue
        cfp_text += "\n".join(list(parent.stripped_strings))

    if len(cfp_text) < len('\n'.join([t.text for t in program_tags])) + 10:
        # if the parent tag contains a small amount of text (e.g. only the
        # heading) return the whole html text
        cfp_text = html.text
    return cfp_text
