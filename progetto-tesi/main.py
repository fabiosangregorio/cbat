import scraper
import extractor

# url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040&copyownerid=12184"

# html = scraper.get_wikiCFP(url)
# program_committee_html = extractor.extract_program_committee(html)

# program_committee = extractor.ner(program_committee_html)

program_committee = ['Xavier Alamán']

for name in program_committee:
    search_result = scraper.search_dblp(name)
    papers = scraper.get_papers_from_dblp(search_result.name_url)