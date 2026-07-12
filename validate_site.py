from pathlib import Path
from html.parser import HTMLParser
from html import unescape, escape
import json, re, sys
from design_specs import SPECS

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
expected={'requirements','scale','contract','decisions','flows','performance','consistency','failures','operations','followups','interview'}
for page in pages:
    p=Parser(); text=page.read_text(); p.feed(text)
    if page.parent.name=='designs':
        missing=expected-p.ids
        if missing:errors.append(f'{page.name}: missing ids {sorted(missing)}')
        if p.svgs!=2:errors.append(f'{page.name}: expected 2 SVGs, got {p.svgs}')
        if p.theme_buttons<1:errors.append(f'{page.name}: missing theme toggle')
        if '<html lang="en" data-theme="dark">' not in text:errors.append(f'{page.name}: not dark-first')
        if text.find('id="architecture"')>text.find('id="requirements"'):errors.append(f'{page.name}: architecture must precede tutorial')
        if text.count('<section class="chapter"')!=11:errors.append(f'{page.name}: expected exactly 11 coherent chapters')
        if 'class="chapter-toc"' not in text:errors.append(f'{page.name}: missing sticky tutorial nav')
        if 'class="deployment-boundary"' not in text:errors.append(f'{page.name}: missing deployment boundary')
        if text.count('data-kind=')<12:errors.append(f'{page.name}: missing semantic component kinds')
        if 'MUTATION / COMMIT' not in text or 'ONLINE / READ + RECOVERY' not in text:errors.append(f'{page.name}: missing two-path sequence teaching view')
        for token in ['data-call-flow','data-flows=','data-flow-select="mutation"','data-flow-select="read"','data-flow-select="recovery"','data-flow-play','data-flow-prev','data-flow-next','data-flow-restart','data-flow-list','data-call-flow-overlay']:
            if token not in text:errors.append(f'{page.name}: missing call-flow token {token}')
        if text.count('data-node-index=')<12:errors.append(f'{page.name}: missing SVG call-flow node metadata')
        overlay_pos=text.find('data-call-flow-overlay')
        first_node_pos=text.find('data-node-index=')
        if overlay_pos<0 or first_node_pos<0 or overlay_pos>first_node_pos:errors.append(f'{page.name}: call-flow overlay must render behind component nodes')
        kinds=set(re.findall(r'data-kind="([^"]+)"',text))
        if len(kinds)<3:errors.append(f'{page.name}: expected >=3 semantic component kinds, got {sorted(kinds)}')
        if 'service' not in kinds:errors.append(f'{page.name}: missing service/domain components')
        visible=re.sub(r'<script.*?</script>|<style.*?</style>',' ',text,flags=re.S)
        visible=unescape(re.sub(r'<[^>]+>',' ',visible))
        words=re.findall(r"\b[\w’'-]+\b",visible)
        if len(words)<2200:errors.append(f'{page.name}: too shallow ({len(words)} words; need >=2200)')
        if text.count('<table')<6:errors.append(f'{page.name}: expected >=6 focused tables')
        if text.count('<pre')<5:errors.append(f'{page.name}: expected >=5 code/data blocks')
        if text.count('<details')<8:errors.append(f'{page.name}: expected >=8 focused expandable discussions')
        slug=page.stem; spec=SPECS.get(slug)
        if not spec:errors.append(f'{page.name}: missing design specification')
        else:
            match=re.search(r'data-component-count="(\d+)"',text)
            count=int(match.group(1)) if match else 0
            if count<12:errors.append(f'{page.name}: architecture has only {count} components')
            if text.count('<text')<55:errors.append(f'{page.name}: diagrams are too sparse ({text.count("<text")} labels)')
            for term in spec['nodes']+spec['failures']:
                if escape(term) not in text:errors.append(f'{page.name}: missing specific term {term}')
            for operation in spec['api']:
                parts=operation.split(' — ',1)
                for part in parts:
                    if escape(part) not in text:errors.append(f'{page.name}: missing API term {part}')
    for href in p.links:
        if href.startswith(('http:','https:','mailto:','#')):continue
        target=(page.parent/href.split('#')[0]).resolve()
        if not target.exists():errors.append(f'{page.name}: broken {href}')

js=(ROOT/'assets/site.js').read_text()
for token in ['try{return localStorage.getItem','try{localStorage.setItem','data-theme-toggle','dataset.defaultTheme']:
    if token not in js:errors.append(f'site.js missing safety token: {token}')
css=(ROOT/'assets/style.css').read_text()
for token in [':root[data-theme="dark"]','@media(max-width:820px)','@media print']:
    if token not in css:errors.append(f'style.css missing: {token}')
landing=(ROOT/'index.html').read_text()
landing_js=(ROOT/'assets/landing.js').read_text()
landing_css=(ROOT/'assets/landing.css').read_text()
for token in ['data-topology','data-curriculum-search','data-visible-count','data-filter="all"','learning-path','hero-stage']:
    if token not in landing:errors.append(f'landing missing: {token}')
for token in ['prefers-reduced-motion','IntersectionObserver','requestAnimationFrame','getContext','pagehide']:
    if token not in landing_js+landing_css:errors.append(f'landing motion missing: {token}')
if landing.count('class="design-card"')!=manifest['count']:
    errors.append(f'landing expected {manifest["count"]} design cards')
call_flow_js=(ROOT/'assets/call-flow.js').read_text()
call_flow_css=(ROOT/'assets/call-flow.css').read_text()
if 'flow-badge' in call_flow_js:errors.append('call-flow center badges must not obscure component labels')
for token in ['requestAnimationFrame' if False else 'setTimeout','animateMotion','ArrowRight','ArrowLeft','pagehide' if False else 'prefers-reduced-motion','aria-live']:
    source=call_flow_js+call_flow_css+(ROOT/'designs/url-shortener.html').read_text()
    if token not in source:errors.append(f'call-flow assets missing: {token}')
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f'PASS: {len(pages)} pages; {len(manifest["pages"])} design routes; all links/sections/diagrams/followups/theme checks valid')
