import requests
from collections import namedtuple
import re

from bs4 import NavigableString

import util.webutil as webutil
from config import HEADINGS, RE_P_PROGRAM_HEADINGS, P_PROGRAM_HEADINGS


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
    """
    Searches the conference website for a program committee, looking in the
    homepage and in secondary pages.
    """
    if not url:
        return None

    html = webutil.get_page(url)['html']
    if not html.text:
        return None
    if not secondary:
        # if a link to the conference's program committee is present, extract the
        # committee from there, otherwise extract it from the main external page.
        program_links = [tag for tag in html('a') if any(h in tag.text.lower()
                         for h in HEADINGS + ["organization"])]
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

    regex = re.compile('.*(' + '|'.join(RE_P_PROGRAM_HEADINGS) + ').*', re.IGNORECASE)
    # tag.parent gets the tag
    program_tags = [tag.parent for tag in html(text=regex)]

    cfp_text = ""
    parent_tags = []
    tags = []
    for tag in program_tags:
        # travel the DOM upwards until other text beside the one in program_tag
        # is found
        parent = tag
        prev_tag = tag
        prev_len = len(tag.text)
        while True:
            parent = parent.parent
            if not parent or len(parent.text) > prev_len + 10:
                break
            prev_len = len(parent.text)
            prev_tag = parent
        parent_tags.append(parent)
        tags.append(prev_tag)

    unique_tags = []
    i = 0
    for parent in parent_tags:
        if i > 0 and parent in parent_tags[:i-1]:
            continue
        unique_tags.append(tags[i])
        i += 1

    for tag in list(set(parent_tags)):
        # get the text from the found tag and all the tags after it
        # (using unique found tags)
        strings = list(tag.stripped_strings)
        for sibling in tag.next_siblings:
            if isinstance(sibling, NavigableString):
                strings.append(sibling)
            else:
                strings += list(sibling.stripped_strings)
        cfp_text += "\n".join(strings)

    if len(cfp_text) < len('\n'.join([t.text for t in program_tags])) + 10:
        # if the parent tag contains a small amount of text (e.g. only the
        # heading) return the whole html text
        cfp_text = html.text
    return webutil.polish_html(cfp_text)
