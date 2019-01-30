import scraper
import program_extractor
from person import Person

# # url con due righe
# # url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040&copyownerid=12184"

# # url con una riga
url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345&copyownerid=75434"
html = scraper.get_wikiCFP(url)

program_committee = program_extractor.extract_program_committee(html)
 

# program_committee = [Person('Kai Chen', 'Chinese Academy of Sciences, China')]

# with open('progetto-tesi/program_test.txt', 'r') as f:
#     data = f.read()

# program_committee = [Person(p.split('#')[0], p.split('#')[1]) for p in data.splitlines()]
# people = list()

# for person in program_committee:
#     people.append({
#         "person_name": person.name,
#         "person_affiliation": person.affiliation,
#         "results": scraper.search_dblp(person)
#     })


# with open('progetto-tesi/results.txt', 'w') as f:
#     for person in people:
#         f.write(f'\n\n================================\nname: {person["person_name"]}, affiliation: {person["person_affiliation"]}\n================================\n')
#         for ratio in person['results']:
#             ratio["results"].sort(reverse=True, key=lambda x: x[1])
#             f.write('\n\n' + ratio["name"] + '\n')
#             f.write("\n".join([": ".join(reversed([str(r) for r in list(res)])) for res in ratio["results"]]))


    # papers = scraper.get_papers_from_dblp(search_result.name_url)