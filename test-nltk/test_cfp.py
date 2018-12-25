import spacy
from spacy import displacy
import en_core_web_sm
import en_core_web_md
import xx_ent_wiki_sm
import time

def test(dict):
  start_time = time.time()
  if dict == 'sm':
    nlp = en_core_web_sm.load()
    per_ee = 'PERSON'
  elif dict == 'md':
    nlp = en_core_web_md.load()
    per_ee = 'PERSON'
  elif dict == 'xx':
    nlp = xx_ent_wiki_sm.load()
    per_ee = 'PER'

  with open('cfp.txt', 'r') as myfile:
    data = myfile.read()

  doc = nlp(data)
  people = [ee for ee in doc.ents if ee.label_ == per_ee]
  people_str = '\n'.join(map(str, people))

  with open(f'processed/{dict}.txt', "w") as text_file:
    text_file.write(people_str)

  compare(people_str, dict, start_time)

def compare(data, filename, start_time):
  with open('real.txt', 'r') as myfile:
    real = myfile.read().split('\n')

  right = []
  wrong = []
  missing = real

  for name in data.split('\n'):
    name = name.rstrip()
    if len(name) == 0:
      continue
    if name in real:
      right.append(name)
      missing.remove(name)
    else:
      wrong.append(name)

  with open(f'compared/{filename}_real_compared.txt', 'w') as f:
    f.write(f'EXECUTION TIME: {time.time() - start_time}\n')
    f.write('RIGHT NAMES:\n')
    f.write('\n'.join(map(str, right)))
    f.write('\n\nWRONG NAMES:\n')
    f.write('\n'.join(map(str, wrong)))
    f.write('\n\nMISSING NAMES:\n')
    f.write('\n'.join(map(str, missing)))

test('sm')
test('md')
test('xx')
