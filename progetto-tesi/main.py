#!/usr/bin/env python3

from multiprocessing import Pool
import time

from bs4 import BeautifulSoup

import webutil

import dblp
import program_extractor
from person import Person

if __name__ == "__main__":
    # # url con due righe
    # # url = "http://www.wikicfp.com/c2fp/servlet/event.showcfp?eventid=10040&copyownerid=12184"

    # # url con una riga
    # url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345&copyownerid=75434"
    # html = dblp.get_wikiCFP(url)

    # program_committee = program_extractor.extract_program_committee(html)
    

    # program_committee = [Person('Kai Chen', 'Chinese Academy of Sciences, China')]
    with open('progetto-tesi/program_test.txt', 'r') as f:
        data = f.read()

    program_committee = [Person(p.split('#')[0], p.split('#')[1]) for p in data.splitlines()]
    people = list()

    start_time = time.time()

    with Pool(5) as p:
        people = p.map(dblp.find_author, program_committee)

    print('Total search of name in dblp: ', time.time() - start_time)


    # for person in program_committee:
    #     dblp.find_author(person)
        # people.append({
        #     "person_name": person.name,
        #     "person_affiliation": person.affiliation,
        #     "result": dblp.find_author(person)['result'] if dblp.find_author(person)['status'] != 'error' else None
        # })


    # with open('progetto-tesi/results.txt', 'w') as f:
    #     for person in people:
    #         f.write(f'\n\n================================\nname: {person["person_name"]}, affiliation: {person["person_affiliation"]}\n================================\n')
    #         for ratio in person['results']:
    #             ratio["results"].sort(reverse=True, key=lambda x: x[1])
    #             f.write('\n\n' + ratio["name"] + '\n')
    #             f.write("\n".join([": ".join(reversed([str(r) for r in list(res)])) for res in ratio["results"]]))


        # papers = dblp.get_papers_from_dblp(search_result.name_url)