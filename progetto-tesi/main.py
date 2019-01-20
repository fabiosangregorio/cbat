import scraper
import extractor

url = "http://www.wikicfp.com/cfp/servlet/event.showcfp?eventid=10040&copyownerid=12184"
html = scraper.get_CFP(url)
program_committee_html = extractor.extract_program_committee(html)
program_committee = extractor.ner(program_committee_html)

with open('test.txt', 'w') as f:
    f.write('\n'.join(program_committee))