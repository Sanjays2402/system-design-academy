from pathlib import Path
from html.parser import HTMLParser
from html import unescape
import json, re, sys

ROOT=Path(__file__).parent/'site'
manifest=json.loads((ROOT/'manifest.json').read_text())
errors=[]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=set(); self.svgs=0; self.titles=[]; self.theme_buttons=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag=='svg':self.svgs+=1
        if tag=='button' and 'data-theme-toggle' in a:self.theme_buttons+=1

pages=[ROOT/'index.html']+sorted((ROOT/'designs').glob('*.html'))
expected_pages=manifest['count']+1
if len(pages)!=expected_pages:errors.append(f'expected {expected_pages} pages, got {len(pages)}')
expected={'requirements','clarify','scale','estimation-math','api','data-model-deep','architecture','components','flow','algorithm','caching','deep-dives','deep-dive-expanded','tradeoffs','reliability','failure-matrix','regions','security-deep','observability-deep','followups','followup-answers','plan','checklist'}
for page in pages:
    p=Parser(); text=page.read_text(); p.feed(text)
    if page.parent.name=='designs':
        missing=expected-p.ids
        if missing:errors.append(f'{page.name}: missing ids {sorted(missing)}')
        if p.svgs!=2:errors.append(f'{page.name}: expected 2 SVGs, got {p.svgs}')
        if text.count('<details class="followup"')<10:errors.append(f'{page.name}: expected >=10 followup/answer sections')
        if p.theme_buttons<1:errors.append(f'{page.name}: missing theme toggle')
        visible=re.sub(r'<script.*?</script>|<style.*?</style>',' ',text,flags=re.S)
        visible=unescape(re.sub(r'<[^>]+>',' ',visible))
        words=re.findall(r"\b[\w’'-]+\b",visible)
        if len(words)<2200:errors.append(f'{page.name}: too shallow ({len(words)} words; need >=2200)')
        if text.count('<table')<7:errors.append(f'{page.name}: expected >=7 tables')
        if text.count('<pre')<3:errors.append(f'{page.name}: expected >=3 code/data blocks')
        if text.count('<details')<13:errors.append(f'{page.name}: expected >=13 expandable deep dives')
    for href in p.links:
        if href.startswith(('http:','https:','mailto:','#')):continue
        target=(page.parent/href.split('#')[0]).resolve()
        if not target.exists():errors.append(f'{page.name}: broken {href}')

js=(ROOT/'assets/site.js').read_text()
for token in ['try{return localStorage.getItem','try{localStorage.setItem','data-theme-toggle',"?saved:'light'"]:
    if token not in js:errors.append(f'site.js missing safety token: {token}')
css=(ROOT/'assets/style.css').read_text()
for token in [':root[data-theme="dark"]','@media(max-width:820px)','@media print']:
    if token not in css:errors.append(f'style.css missing: {token}')
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f'PASS: {len(pages)} pages; {len(manifest["pages"])} design routes; all links/sections/diagrams/followups/theme checks valid')
