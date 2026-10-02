#!/usr/bin/env python3
"""Build RobotOps Twin's documentation. This does not run a robot simulator.

Inputs: reports/*.md, publication/references.json, diagrams.json, style.css.
Outputs: _site (static website, source downloads, three PDFs and combined PDF).
All graphics are original vectors generated from editable diagram definitions.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from markdown_it import MarkdownIt
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
DATE = '2026-10-01'
VERSION = '1.0.0'
REPO = 'raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator'
REPO_URL = 'https://github.com/' + REPO
REPORTS = [
    {'slug':'01-design', 'page':'design', 'number':'01',
     'title':'Från kundorder till verifierad roboteffekt',
     'subtitle':'Vetenskaplig designstudie för RobotOps Twin',
     'description':'Forskningsunderlag, kravspårbarhet, arkitektur, kontrakt och en förhandsdefinierad utvärderingsplan.'},
    {'slug':'02-avgransning', 'page':'avgransning', 'number':'02',
     'title':'Simulatorn och den verkliga robotcellen',
     'subtitle':'Avgränsning, realism och överförbarhet',
     'description':'Vad demonstratorn kan representera, vad den inte kan bevisa och vad som krävs före fysisk integration.'},
    {'slug':'03-diskussion', 'page':'diskussion', 'number':'03',
     'title':'Teknisk dialog om RobotOps Twin',
     'subtitle':'Diskussionsunderlag för Axel Kaliff och Per-Eric Olsson',
     'description':'Öppningsberättelse, källgrundade frågor, tekniska avvägningar, whiteboardfall och samtalsprotokoll.'},
]
PALETTE = {
    'business':('#eef2f6','#182f43'),
    'core':('#edf6f5','#126b70'),
    'world':('#f2f0f8','#63577a'),
    'warn':('#fbf4e6','#896321'),
}
E = html.escape


def read_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')


def svg_text(x: float, y: float, text: str, size: float=18,
             anchor: str='start', color: str='#182f43', weight: str='400') -> str:
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size:g}" '
            f'text-anchor="{anchor}" fill="{color}" font-weight="{weight}">'
            f'{E(text)}</text>')


def edge_path(a: list[Any], b: list[Any], nodes: list[list[Any]]) -> str:
    ax,ay,aw,ah = map(float,a[1:5]); bx,by,bw,bh = map(float,b[1:5])
    acx,acy=ax+aw/2,ay+ah/2; bcx,bcy=bx+bw/2,by+bh/2
    if abs(acy-bcy)<2:
        sx=ax+aw if bcx>acx else ax; tx=bx if bcx>acx else bx+bw
        return f'M {sx:g} {acy:g} L {tx:g} {bcy:g}'
    if abs(acx-bcx)<2:
        between=[n for n in nodes if n[0] not in (a[0],b[0])
                 and abs(n[1]+n[3]/2-acx)<2
                 and min(acy,bcy)<n[2]+n[4]/2<max(acy,bcy)]
        if between:
            route=max(ax+aw,bx+bw)+28
            return f'M {ax+aw:g} {acy:g} H {route:g} V {bcy:g} H {bx+bw:g}'
        sy=ay+ah if bcy>acy else ay; ty=by if bcy>acy else by+bh
        return f'M {acx:g} {sy:g} V {ty:g}'
    sy=ay+ah if bcy>acy else ay; ty=by if bcy>acy else by+bh
    mid=(sy+ty)/2
    return f'M {acx:g} {sy:g} V {mid:g} H {bcx:g} V {ty:g}'


def render_diagram(name: str, d: dict[str,Any]) -> tuple[str,str]:
    w,h=d['width'],d['height']
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           f'<title id="title">{E(d["title"])}</title><desc id="desc">{E(d["caption"])}</desc>',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#526473"/></marker><marker id="red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#a34838"/></marker></defs>',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g font-family="DejaVu Sans, Arial, sans-serif">',
           svg_text(28,34,d['title'],23,weight='700'),
           svg_text(28,62,d['subtitle'],16,color='#526473')]
    mermaid=[]
    if d.get('type')=='sequence':
        mermaid=['sequenceDiagram']
        pos={p[0]:p[2] for p in d['participants']}
        for key,label,x in d['participants']:
            parts += [f'<rect x="{x-95}" y="90" width="190" height="48" rx="6" fill="#edf6f5" stroke="#a5c6c7"/>',
                      svg_text(x,120,label,19,'middle',weight='700'),
                      f'<path d="M {x} 140 V 710" stroke="#c3d0d8" stroke-dasharray="6 6"/>']
            mermaid.append(f'  participant {key} as {label}')
        for start,end,y,label,kind in d['messages']:
            sx,tx=pos[start],pos[end]
            if kind=='note':
                xx=max(20,min(w-330,sx-150))
                parts += [f'<rect x="{xx}" y="{y-23}" width="310" height="43" rx="4" fill="#fbf4e6" stroke="#d7c192"/>',
                          svg_text(xx+155,y+4,label,16,'middle')]
                mermaid.append(f'  Note over {start}: {label}')
            else:
                lost=kind=='lost'; color='#a34838' if lost else '#526473'
                marker='red' if lost else 'arrow'
                dash=' stroke-dasharray="7 5"' if lost else ''
                parts += [f'<path d="M {sx} {y} H {tx}" stroke="{color}" stroke-width="2" marker-end="url(#{marker})"{dash}/>',
                          svg_text((sx+tx)/2,y-12,label,16,'middle',color)]
                if lost:
                    cx=(sx+tx)/2
                    parts.append(f'<path d="M {cx-7} {y-7} l 14 14 M {cx-7} {y+7} l 14 -14" stroke="#a34838" stroke-width="3"/>')
                mermaid.append(f'  {start}{"--x" if lost else "->>"}{end}: {label}')
        parts += [svg_text(28,755,'Ingen ny PICK skickas under avstämningen.',18,color='#126b70',weight='700')]
    else:
        mermaid=['flowchart TD']
        lookup={n[0]:n for n in d['nodes']}
        for edge in d['edges']:
            a,b=lookup[edge[0]],lookup[edge[1]]
            mode=edge[2] if len(edge)>2 else 'normal'
            dash=' stroke-dasharray="7 5"' if mode=='dashed' else ''
            both=' marker-start="url(#arrow)"' if mode=='both' else ''
            parts.append(f'<path d="{edge_path(a,b,d["nodes"])}" fill="none" stroke="#526473" stroke-width="2" marker-end="url(#arrow)"{both}{dash}/>')
        for n in d['nodes']:
            key,x,y,nw,nh,title,description,kind=n
            bg,stroke=PALETTE[kind]
            parts += [f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="7" fill="{bg}" stroke="{stroke}" stroke-width="1.3"/>',
                      f'<rect x="{x}" y="{y+10}" width="4" height="{nh-20}" rx="2" fill="{stroke}"/>']
            titlelines=textwrap.wrap(title,width=max(17,int((nw-32)/11.0)),break_long_words=False)
            desclines=textwrap.wrap(description,width=max(21,int((nw-32)/8.7)),break_long_words=False)
            total=len(titlelines)*23+len(desclines)*21+6
            yy=y+(nh-total)/2+19
            for line in titlelines:
                parts.append(svg_text(x+nw/2,yy,line,19,'middle',weight='700')); yy+=23
            yy+=3
            for line in desclines:
                parts.append(svg_text(x+nw/2,yy,line,16,'middle',color='#526473')); yy+=21
            mt=title.replace('"',"'")+ '<br/>'+description.replace('"',"'")
            mermaid.append(f'  {key}["{mt}"]')
        for edge in d['edges']:
            mode=edge[2] if len(edge)>2 else 'normal'
            arrow={'normal':'-->','both':'<-->','dashed':'-.->'}[mode]
            mermaid.append(f'  {edge[0]} {arrow} {edge[1]}')
        if d.get('footer'):
            for i,line in enumerate(textwrap.wrap(d['footer'],width=98)):
                parts.append(svg_text(28,h-22+i*19,line,15,color='#526473'))
    parts += ['</g></svg>']
    svg='\n'.join(parts)
    ElementTree.fromstring(svg)
    return svg,'\n'.join(mermaid)+'\n'


def figure(name: str, diagrams: dict[str,Any]) -> str:
    d=diagrams[name]
    return (f'<figure id="fig-{E(name)}"><img src="assets/{E(name)}.svg" '
            f'alt="{E(d["title"])}. {E(d["caption"])}" width="{d["width"]}" height="{d["height"]}">'
            f'<figcaption>{E(d["caption"])}</figcaption>'
            f'<div class="figure-tools"><a href="assets/{E(name)}.svg">Öppna stor SVG</a>'
            f'<a href="sources/diagrams/{E(name)}.mmd" download>Mermaid-källa</a>'
            f'<a href="sources/diagrams.json" download>Redigera layout (JSON)</a></div></figure>')


def reference_html(s: dict[str,str]) -> str:
    additional=''
    if s.get('corroboration'):
        u=E(s['corroboration'])
        additional=f'<p class="ref-url">Kompletterande primärkälla: <a href="{u}">{u}</a></p>'
    return (f'<section class="reference" id="ref-{s["id"]}">'
            f'<h3>[{s["id"]}] {E(s["title"])}</h3>'
            f'<span class="ref-kind">{E(s["kind"])}</span>'
            f'<p>{E(s["author"])}. {E(s["date"])}. Kontrollerad {DATE}.</p>'
            f'<p class="ref-url"><a href="{E(s["url"])}">{E(s["url"])}</a></p>'
            f'<p>{E(s["note"])}</p>{additional}</section>')


def header(current: str) -> str:
    links=[('index','Översikt'),('design','Designstudie'),('avgransning','Avgränsning'),('diskussion','Diskussion'),('kallor','Källor'),('diagram','Diagram')]
    nav=''.join(f'<a href="{p}.html"'+(' aria-current="page"' if p==current else '')+f'>{t}</a>' for p,t in links)
    return ('<a class="skip" href="#main">Hoppa till innehållet</a><header class="site-header">'
            '<a class="brand" href="index.html">ROBOTOPS TWIN<span>FORSKNING · SYSTEMDESIGN · DIALOG</span></a>'
            f'<nav class="top-nav" aria-label="Huvudmeny">{nav}</nav></header>')


def page(title: str, content: str, current: str, description: str='') -> str:
    return ('<!doctype html><html lang="sv"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{E(title)} | RobotOps Twin</title><meta name="author" content="Rami Halabi">'
            f'<meta name="description" content="{E(description or title)}">'
            '<link rel="stylesheet" href="style.css"></head><body>' + header(current)+content+
            '<footer class="site-footer">Rami Halabi · Version 1.0 · 1 oktober 2026.<br>'
            'Oberoende, AI-assisterad designstudie. Inte SICS AI:s dokumentation eller en verifierad robotimplementation. '
            f'<a href="{REPO_URL}">Källfiler på GitHub</a> · '
            '<a href="downloads/robotops-twin-samlat.pdf">Samtliga rapporter som PDF</a></footer></body></html>')


def build_report(meta: dict[str,str], refs: dict[str,Any], diagrams: dict[str,Any]) -> tuple[str,list[str],int]:
    raw=(ROOT/'reports'/f'{meta["slug"]}.md').read_text(encoding='utf-8')
    raw=re.sub(r'\[S(\d{2})[–-]S(\d{2})\]',lambda m: ''.join(f'[S{i:02}]' for i in range(int(m[1]),int(m[2])+1)),raw)
    used=sorted(set(re.findall(r'\[(S\d{2})\]',raw)))
    unknown=set(used)-refs.keys()
    if unknown:
        raise ValueError(f'Unknown reference IDs: {unknown}')
    md=MarkdownIt('commonmark',{'html':True}).enable('table')
    tokens=md.parse(raw)
    toc=[]; heading_number=0
    for i,t in enumerate(tokens):
        if t.type=='heading_open':
            heading_number+=1
            ident=f'section-{heading_number}'
            t.attrSet('id',ident)
            if t.tag=='h2':
                title=tokens[i+1].content
                toc.append((ident,title))
    body=md.renderer.render(tokens,md.options,{})
    body=re.sub(r'<p>\{\{figure:([a-z-]+)\}\}</p>',lambda m: figure(m[1],diagrams),body)
    body=re.sub(r'\[(S\d{2})\]',lambda m: f'<a class="cite" href="#ref-{m[1]}" aria-label="Källa {m[1]}">[{m[1]}]</a>',body)
    body=body.replace('<table>','<div class="table-scroll"><table>').replace('</table>','</table></div>')
    if '{{figure:' in body:
        raise ValueError('Unresolved figure placeholder')
    refs_html='<section class="references" aria-label="Referenser"><h2 id="referenser">Referenser och källbegränsningar</h2>'
    refs_html+='<p>Referenserna avser avgränsade sakuppgifter. Diagram, kontrakt och testplan är egna förslag. Gemensamt kontrolldatum: 1 oktober 2026.</p>'
    refs_html+=''.join(reference_html(refs[k]) for k in used)+'</section>'
    toc.append(('referenser','Referenser och källbegränsningar'))
    toc_list='<ol>'+''.join(f'<li><a href="#{i}">{E(t)}</a></li>' for i,t in toc)+'</ol>'
    sidebar='<aside class="sidebar"><details open><summary>Innehåll</summary>'+toc_list+'</details><div class="side-meta">'
    sidebar+=f'Rapport {meta["number"]} / 03<br>Version 1.0 · Svenska<br>Designstadium — inga driftresultat<br><a href="downloads/{meta["slug"]}.pdf">Ladda ned PDF</a></div></aside>'
    cover=f'<section class="cover"><div class="eyebrow">Rapport {meta["number"]} / 03 · RobotOps Twin</div><h1>{E(meta["title"])}</h1>'
    cover+=f'<p class="subtitle">{E(meta["subtitle"])}</p><div class="metadata">Rami Halabi<br>Version 1.0 · 1 oktober 2026<br>Oberoende tekniskt rapportpaket · Svenska</div>'
    cover+='<div class="status"><strong>Status: design och forskningsunderlag.</strong> Simulatorn beskrivs som ett planerat system. Inga empiriska robotresultat eller säkerhetsgarantier hävdas.</div>'
    cover+=f'<div class="buttons"><a class="button" href="downloads/{meta["slug"]}.pdf" download>Ladda ned PDF</a><a class="button secondary" href="sources/{meta["slug"]}.md" download>Markdown-källa</a></div>'
    cover+='<p class="print-label">AI-assisterad text- och publiceringsframställning.<br>Ej sakkunniggranskad. Inte framtagen av eller godkänd av SICS AI.<br>Rapporternas källor, diagram och byggskript finns i projektets repository.</p></section>'
    content='<div class="shell">'+sidebar+'<main id="main" class="document">'+cover+'<nav class="print-toc" aria-label="Innehållsförteckning"><h2>Innehåll</h2>'+toc_list+'</nav>'+body+refs_html+'</main></div>'
    return page(meta['title'],content,meta['page'],meta['description']),used,len(raw.split())


def validate_links() -> None:
    """Reject broken relative page/assets/download links and missing fragments."""
    from urllib.parse import urlsplit, unquote
    for file in OUT.glob('*.html'):
        text=file.read_text(encoding='utf-8')
        for link in re.findall(r'(?:href|src)="([^"]+)"',text):
            link=html.unescape(link); parsed=urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target=(file.parent/unquote(parsed.path)).resolve() if parsed.path else file
            if not target.exists():
                raise ValueError(f'Broken link in {file.name}: {link}')
            if parsed.fragment and target.suffix=='.html':
                if f'id="{parsed.fragment}"' not in target.read_text(encoding='utf-8'):
                    raise ValueError(f'Missing fragment: {file.name} -> {link}')


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT/'assets').mkdir(parents=True)
    (OUT/'downloads').mkdir()
    (OUT/'sources'/'diagrams').mkdir(parents=True)
    shutil.copy2(ROOT/'publication/style.css',OUT/'style.css')
    references=read_json('publication/references.json'); refs={s['id']:s for s in references}
    diagrams=read_json('publication/diagrams.json')
    for name,d in diagrams.items():
        svg,mmd=render_diagram(name,d)
        write(OUT/'assets'/f'{name}.svg',svg)
        write(OUT/'sources'/'diagrams'/f'{name}.mmd',mmd)
    shutil.copy2(ROOT/'publication/diagrams.json',OUT/'sources/diagrams.json')
    shutil.copy2(ROOT/'publication/references.json',OUT/'sources/references.json')
    if (ROOT/'CITATION.cff').exists():
        shutil.copy2(ROOT/'CITATION.cff',OUT/'sources/CITATION.cff')
    bib=[]
    for s in references:
        title=s['title'].replace('{','').replace('}','')
        bib.append('@misc{'+s['id']+',\n  author = {{'+s['author']+'}},\n  title = {{'+title+'}},\n  url = {'+s['url']+'},\n  urldate = {'+DATE+'},\n  note = {'+s['date']+'; '+s['kind']+'}\n}')
    write(OUT/'sources/references.bib','\n\n'.join(bib)+'\n')
    stats=[]
    for meta in REPORTS:
        doc,used,words=build_report(meta,refs,diagrams)
        file=OUT/f'{meta["page"]}.html'; write(file,doc)
        shutil.copy2(ROOT/'reports'/f'{meta["slug"]}.md',OUT/'sources'/f'{meta["slug"]}.md')
        pdf=OUT/'downloads'/f'{meta["slug"]}.pdf'
        HTML(filename=str(file),base_url=str(OUT)).write_pdf(str(pdf),pdf_tags=True)
        reader=PdfReader(str(pdf))
        extracted='\n'.join(p.extract_text() or '' for p in reader.pages)
        if len(extracted)<1000 or '{{figure:' in extracted:
            raise ValueError(f'Invalid PDF content: {pdf}')
        stats.append({'report':meta['slug'],'title':meta['title'],'pages':len(reader.pages),'words_approx':words,'references':used,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()})
        print(f'Built {pdf.name}: {len(reader.pages)} pages, ~{words} words',flush=True)
    writer=PdfWriter()
    for meta in REPORTS:
        writer.append(str(OUT/'downloads'/f'{meta["slug"]}.pdf'),outline_item=meta['title'])
    writer.add_metadata({'/Title':'RobotOps Twin — samlat rapportpaket','/Author':'Rami Halabi','/Subject':'Designstudie, avgränsning och diskussionsunderlag; inga empiriska robotresultat.'})
    with (OUT/'downloads/robotops-twin-samlat.pdf').open('wb') as f:
        writer.write(f)
    cards=''
    for m,s in zip(REPORTS,stats):
        cards+=f'<article class="card"><div class="number">RAPPORT {m["number"]} · {s["pages"]} SIDOR</div><h2>{E(m["title"])}</h2><p>{E(m["description"])}</p><div class="buttons"><a class="button" href="{m["page"]}.html">Läs rapporten</a><a class="button secondary" href="downloads/{m["slug"]}.pdf" download>PDF</a></div></article>'
    home='<main id="main" class="home"><section class="home-hero"><div class="eyebrow">Oberoende designstudie · version 1.0 · 1 oktober 2026</div><h1>Från order.<br>Till belagd effekt.</h1><p class="lead">Ett forskningsbaserat rapportpaket om systemet mellan kundens lagerorder, AI-förslaget och robotens verkliga resultat — med Blender som planerad simulatorvärld.</p><div class="buttons"><a class="button" href="design.html">Börja med designstudien</a><a class="button secondary" href="downloads/robotops-twin-samlat.pdf" download>Hela paketet som PDF</a></div><div class="status"><strong>Det här är dokumentation, inte en levande robotsimulator.</strong> Rapportpaketet skiljer källbelagda uppgifter från egna designval. Ingen intern SICS-arkitektur, AGI-förmåga eller fysisk säkerhet påstås vara återskapad.</div></section><section aria-label="Rapporter" class="cards">'+cards+'</section><h2>En sammanhängande kedja — flera olika ansvar</h2><p class="section-intro">Alla sju diagram är egna, redigerbara illustrationer. De finns både som vektorgrafik och Mermaid-källor.</p>'+figure('context',diagrams)+'<div class="buttons"><a class="button secondary" href="diagram.html">Utforska alla diagram</a><a class="button secondary" href="kallor.html">Källor och metod</a></div><h2>Läs med rätt förväntningar</h2><p>Designrapporten specificerar vad som ska byggas och testas. Avgränsningsrapporten förklarar vad som inte överförs till en fysisk robotcell. Diskussionsunderlaget hjälper till att pröva antaganden med tekniska sakkunniga.</p><p>Forskningsinspirationen kommer från bland annat CloudGripper/AutoGrasper och R900. Företags- och leverantörsuppgifter redovisas som sådana. Källornas begränsningar följer med in i varje rapport.</p></main>'
    status=read_json('publication/status.json')
    governance_files=['PROJECT_PLAN.md','SUCCESS_CRITERIA.md','HANDOFF.md','CODEX_GOAL_CHECKLIST.md','GOAL_PROGRESS.md','ACCEPTANCE_REPORT.md','README.md','PUBLICATION.md']
    links=''
    for name in governance_files:
        shutil.copy2(ROOT/name,OUT/'sources'/name)
        links+=f'<li><a href="sources/{name}">{name}</a></li>'
    governance='<main id="main" class="catalog"><h1>Implementation and acceptance</h1><div class="status"><strong>'+E(status['status'])+' — '+E(status['phase'])+'</strong><p>'+E(status['summary'])+'</p></div><p>These are current source documents. Historical research is not runtime acceptance evidence. Pages hosts documentation only.</p><ul>'+links+'</ul></main>'
    write(OUT/'governance.html',page('Implementation and acceptance',governance,'governance'))
    home=home.replace('</main>','<h2>Current implementation status</h2><p>'+E(status['status'])+' — '+E(status['summary'])+'</p><p><a href="governance.html">Normative contracts, progress and acceptance evidence</a></p></main>')
    write(OUT/'index.html',page('Forskningsunderlag och systemdesign',home,'index'))
    sources='<main id="main" class="catalog"><div class="eyebrow">Spårbarhet och källkritik</div><h1>Källor, inte antaganden</h1><p>Gemensamt kontrolldatum: 1 oktober 2026. Registret innehåller 20 källor, inklusive kompletterande läsning. Uppgifter från företag och leverantörer är inte likställda med oberoende experiment. Varje rapport visar de källor som faktiskt används där.</p><div class="status">Källorna motiverar avgränsade fynd. Diagrammen, arkitekturen och experimentplanen är egna förslag. Fulltexten till Axels examensarbete kunde inte återhämtas; endast den bibliografiska kopplingen används.</div><div class="buttons"><a class="button secondary" href="sources/references.bib" download>BibTeX</a><a class="button secondary" href="sources/references.json" download>Källregister JSON</a></div><section class="references">'+''.join(reference_html(s) for s in references)+'</section></main>'
    sources=sources.replace('20 källor',str(len(references))+' källor')
    write(OUT/'kallor.html',page('Källregister',sources,'kallor'))
    gallery='<main id="main" class="catalog"><div class="eyebrow">Sju egna illustrationer</div><h1>Systemet, gränserna och felvägen</h1><p>Öppna en figur i storlek som passar skärmen, eller ladda ned dess redigerbara källa. SVG-filerna är också inbäddade som vektorgrafik i PDF-rapporterna.</p><div class="gallery">'+''.join(figure(name,diagrams) for name in diagrams)+'</div></main>'
    write(OUT/'diagram.html',page('Diagramgalleri',gallery,'diagram'))
    write(OUT/'.nojekyll','')
    commit=os.environ.get('GITHUB_SHA','')
    if not commit:
        try:
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        except (OSError,subprocess.SubprocessError):
            commit='local-unversioned-build'
    manifest={'title':'RobotOps Twin publication','version':VERSION,'date':DATE,'source_commit':commit,'reports':stats,'diagrams':len(diagrams),'references':len(references),'combined_pdf_pages':sum(s['pages'] for s in stats),'simulator_status':status,'checks':['reference IDs resolved','figure placeholders resolved','SVG XML parsed','PDF text extractable','relative links and fragments validated']}
    write(OUT/'build.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    validate_links()
    print(json.dumps(manifest,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    main()
