# gets the whole CFP from wikiCFP, as well as the external url of the conference
def get_cfp(url):
    html = webutil.get_page(url)['html']
    if not html.text:
        return None
    
    ext_sources = [a['href'] for a in html.select('.contsec tr:nth-child(3) a') 
        if '/cfp/' not in a['href']]
    external_source = ext_sources[0] if (len(ext_sources) > 0 and 
        'mailto:' not in ext_sources[0]) else None
    cfp_text = webutil.polish_html("".join(
        [tag.getText() for tag in html.select('table .cfp')]))
    cfp = namedtuple('Cfp', 'cfp_text external_source')
    return cfp(cfp_text, external_source)


def search_external_cfp(url, secondary=False):
    if not url:
        return None

    html = webutil.get_page(url)['html']
    if not html.text:
        return None
    # if a link to the conference's program committee is present, extract the 
    # committee from there, otherwise extract it from the main external page.
    if not secondary:
        program_links = [tag for tag in html('a') 
            if any(h in tag.text.lower() for h in headings)]
        if len(program_links):
            link = None
            # if there's a link with the words "program committee" take that one,
            # otherwise just "committee" is ok
            for l in program_links:
                if any(p in l.text.lower() for p in p_program_headings):
                    link = l
                    break
            if not link:
                link = program_links[0]
            full_url = requests.compat.urljoin(url, link['href'])
            return _search_external_cfp(full_url, secondary=True)
            
    regex = re.compile('.*(' + '|'.join(p_program_headings) + ').*', re.IGNORECASE)
    program_tags = [tag.parent for tag in html.body(text=regex)] # tag.parent gets the tag

    cfp_text = ""
    # get unique parents of the tags (if several tags have the same parent, 
    # keep only one)
    for tag in program_tags:
        parent = tag.parent
        if any(t in parent for t in program_tags if t != tag):
            continue
        cfp_text += "\n".join(list(parent.stripped_strings))

    # if the parent tag contains a small amount of text (e.g. only the heading)
    # return the whole html text
    if len(cfp_text) < len('\n'.join([t.text for t in program_tags])) + 10:
        cfp_text = html.text
    return cfp_text
