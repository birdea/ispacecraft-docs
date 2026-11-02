"""Render this repository's Markdown subset with Python 3 only."""
from pathlib import Path
import html
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
SOURCES = [ROOT/'README.md', *sorted((ROOT/'docs').glob('*.md'))]
def target(p):
    return ROOT/'index.html' if p.name == 'README.md' else p.with_suffix('.html')
def inline(s):
    s = html.escape(s)
    def link(m):
        label, url = m.groups()
        if url.endswith('.md'): url = url[:-3]+'.html'
        return f'<a href="{url}">{label}</a>'
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
def body(text):
    out, headings = [], []
    for block in re.split(r'\n\s*\n', text.strip()):
        lines = block.splitlines()
        h = re.fullmatch(r'(#{1,3}) (.+)', block)
        if h:
            level, title, anchor = len(h[1]), h[2], f'section-{len(headings)}'
            headings.append((level,title,anchor))
            out.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
        elif lines[0].startswith('|'):
            rows = [[c.strip() for c in row.strip('|').split('|')] for row in lines]
            rows = [row for row in rows if not all(re.fullmatch(r':?-+:?',c) for c in row)]
            head = ''.join(f'<th scope="col">{inline(c)}</th>' for c in rows[0])
            cells = ''.join('<tr>'+''.join(f'<td>{inline(c)}</td>' for c in row)+'</tr>' for row in rows[1:])
            out.append(f'<div class="table-wrap" role="region" aria-label="{html.escape(rows[0][0])} 표" tabindex="0"><table><thead><tr>{head}</tr></thead><tbody>{cells}</tbody></table></div>')
        elif re.match(r'^(?:- |\d+\. )',lines[0]):
            tag = 'ul' if lines[0].startswith('- ') else 'ol'
            items = ''.join('<li>'+inline(re.sub(r'^(?:- |\d+\. )','',line))+'</li>' for line in lines)
            out.append(f'<{tag}>{items}</{tag}>')
        else: out.append('<p>'+inline(' '.join(lines))+'</p>')
    return '\n'.join(out), headings
def render(source):
    content, headings = body(source.read_text())
    prefix = '' if source.name == 'README.md' else '../'
    title = headings[0][1]
    nav = []
    for other in SOURCES:
        href = prefix+target(other).relative_to(ROOT).as_posix()
        label = '문서 홈' if other.name == 'README.md' else other.read_text().splitlines()[0][2:]
        current = ' aria-current="page"' if source == other else ''
        nav.append(f'<a href="{href}"{current}>{html.escape(label)}</a>')
    toc = ''.join(f'<a href="#{anchor}">{html.escape(label)}</a>' for level,label,anchor in headings if level == 2)
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="ispacecraft 공개 소개 문서: 기획, 디자인, 개발, 우주선 공학, 과학과 세계관.">
<meta name="color-scheme" content="dark">
<title>{html.escape(title)} · ispacecraft</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<a class="skip" href="#content">본문으로 이동</a>
<header><a class="brand" href="{prefix}index.html">ispacecraft<span>FIELD NOTES / 공개 문서</span></a><a href="https://ispacecraft.com">프로젝트 열기 ↗</a></header>
<div class="layout">
<aside><details open><summary>문서 탐색</summary><nav aria-label="분야별 문서">{''.join(nav)}</nav></details></aside>
<main id="content"><div class="eyebrow">BIRDEA / 2026.11.02</div><article>{content}</article><footer><a href="{source.name}">Markdown 원문</a> · © 2026 birdea. All rights reserved.</footer></main>
<nav class="toc" aria-label="이 페이지 목차"><span>이 페이지</span>{toc}</nav>
</div>
</body>
</html>
'''
def build(check=False):
    stale=[]
    for source in SOURCES:
        path, content = target(source), render(source)
        if check:
            if not path.exists() or path.read_text()!=content: stale.append(str(path.relative_to(ROOT)))
        else: path.write_text(content)
    if stale: raise SystemExit('Regenerate HTML: '+', '.join(stale))
    print(f'{len(SOURCES)} HTML pages '+('verified' if check else 'generated'))
if __name__=='__main__': build('--check' in sys.argv)
