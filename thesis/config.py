HEADINGS = ["committee", "commission"]
PROGRAM_HEADINGS = ["program", "programme", "review"]
P_PROGRAM_HEADINGS = [f'{ph} {h}' for h in HEADINGS for ph in PROGRAM_HEADINGS]
RE_P_PROGRAM_HEADINGS = [f'{ph}.*{h}' for h in HEADINGS for ph in PROGRAM_HEADINGS]
NER_LOSS_THRESHOLD = 0.7
CONF_EDITIONS_LOWER_BOUNDARY = 5
