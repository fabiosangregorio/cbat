import scraper
import extractor
from person import Person

# # url con due righe
# # url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040&copyownerid=12184"

# # url con una riga
# url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=52345&copyownerid=75434"

# html = scraper.get_wikiCFP(url)
# program_committee_html = extractor.extract_program_committees(html)

# program_committee = extractor.ner(program_committee_html)

# program_committee = program_committee[0:0]
program_committee = [Person('Kai Chen', 'Chinese Academy of Sciences, China')]

for person in program_committee:
    search_result = scraper.search_dblp(person)
    papers = scraper.get_papers_from_dblp(search_result.name_url)