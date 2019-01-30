# NOT WORKING, it's just an explanation of how I chose the scorer for fuzzywuzzy

def search_dblp(person):
    start_time = time.time()

    base_url = "https://dblp.org/search"
    query = urllib.parse.urlencode({"q": person.name})
    response = get_page(base_url + '/author?' + query)
    # request at /author gets redirected if the author is an exact match on the url. 
    # To be sure about it being the right one, we want to make it go through the same process as the other authors
    if response["redirected"]:
        response = get_page(base_url + '?' + query)

    html = BeautifulSoup(response["html"], 'html.parser')

    is_exact = html.select("#completesearch-authors > .body p")[0].getText().lower() == "exact matches"

    # first ul, either contains the exact matches or likely matches
    search_results = list()
    for li in html.select("#completesearch-authors > .body ul")[0].select('li'):
        search_results.append({ 
            "name": " ".join([m.getText() for m in li.select('a mark')]),
            "affiliation": li.select('small')[0].getText() if li.select('small') else "",
            "url": li.select('a')[0]['href']
        })
    print('Search of name in dblp: ', time.time() - start_time)
    return [
        {"name": "ratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.ratio, limit=20)},
        {"name": "partial_ratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.partial_ratio, limit=20)},
        {"name": "token_sort_ratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.token_sort_ratio, limit=20)},
        {"name": "partial_token_sort_ratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.partial_token_sort_ratio, limit=20)},
        {"name": "token_set_ratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.token_set_ratio, limit=20)},
        {"name": "partial_token_set_ratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.partial_token_set_ratio, limit=20)},
        {"name": "qratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.QRatio, limit=20)},
        {"name": "wratio", "results": process.extract(person.affiliation, [r["affiliation"] for r in search_results], scorer=fuzz.WRatio, limit=20)}
    ]


with open('progetto-tesi/program_test.txt', 'r') as f:
    data = f.read()

program_committee = [Person(p.split('#')[0], p.split('#')[1]) for p in data.splitlines()]
people = list()

for person in program_committee:
    people.append({
        "person_name": person.name,
        "person_affiliation": person.affiliation,
        "results": scraper.search_dblp(person)
    })


with open('progetto-tesi/results.txt', 'w') as f:
    for person in people:
        f.write(f'\n\n================================\nname: {person["person_name"]}, affiliation: {person["person_affiliation"]}\n================================\n')
        for ratio in person['results']:
            ratio["results"].sort(reverse=True, key=lambda x: x[1])
            f.write('\n\n' + ratio["name"] + '\n')
            f.write("\n".join([": ".join(reversed([str(r) for r in list(res)])) for res in ratio["results"]]))