DB_NAME = 'cbat'
HEADINGS = ["committee", "commission"]
PROGRAM_HEADINGS = ["program", "programme", "review"]
NER_LOSS_THRESHOLD = 0.7
CONF_EDITIONS_LOWER_BOUNDARY = 5
CONF_EXCLUDE_CURR_YEAR = True
AUTH_NO_AFFILIATION_RATIO = 0.5
AUTH_NOT_EXACT_RATIO = 0.5
MIN_COMMITTEE_SIZE = 5
SPACY_MODEL = 'en_core_web_sm'
WIKICFP_BASE_URL = 'http://www.wikicfp.com'

P_PROGRAM_HEADINGS = [f'{ph} {h}' for h in HEADINGS for ph in PROGRAM_HEADINGS]
RE_P_PROGRAM_HEADINGS = [f'{ph}.*{h}' for h in HEADINGS for ph in PROGRAM_HEADINGS]
