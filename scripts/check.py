"""Check generated pages, local links and common disclosure mistakes."""
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re
from build import ROOT, SOURCES, build
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links,self.ids=[],[]
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        for key in ('href','src'):
            if key in attrs:self.links.append(attrs[key])
build(check=True)
pages={p:Page(p.read_text()) for p in ROOT.rglob('*.html')}
errors=[]
count=0
for path,page in pages.items():
    if len(page.ids)!=len(set(page.ids)):errors.append(f'{path}: duplicate IDs')
    for link in page.links:
        url=urlsplit(link)
        if url.scheme or url.netloc:continue
        count+=1
        dest=(path.parent/unquote(url.path)).resolve() if url.path else path
        if not dest.is_relative_to(ROOT) or not dest.is_file():errors.append(f'{path.name}: missing/escaping link {link}')
        elif url.fragment and dest in pages and unquote(url.fragment) not in pages[dest].ids:errors.append(f'{path.name}: missing anchor {link}')
for source in SOURCES:
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',source.read_text()):
        if not urlsplit(link).scheme and not (source.parent/link).is_file():errors.append(f'{source.name}: missing Markdown link {link}')
    for pattern in [r'태양\s*광석',r'(?i)solar ore',r'/Users/',r'/private/',r'(?i)api[_-]?token',r'BEGIN .*PRIVATE KEY',r'github\.com/birdea/ispacecraft(?:\.git|/|[)\s])']:
        if re.search(pattern,source.read_text()):errors.append(f'{source.name}: review outdated/private text matching {pattern}')
if errors:raise SystemExit('\n'.join(errors))
print(f'{len(SOURCES)} Markdown sources, {len(pages)} HTML pages, {count} local HTML references verified')
