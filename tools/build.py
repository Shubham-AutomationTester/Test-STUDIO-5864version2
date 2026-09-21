#!/usr/bin/env python3
"""Build the committed static site and host-specific HTTP rules. No dependencies."""
import argparse
import csv
import html
import json
import posixpath
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
from cases import make_cases, TICKET
OUT = ROOT / 'docs'
QA = ROOT / 'qa'

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

def relative(source, target):
    start = source if source.endswith('/') else posixpath.dirname(source) + '/'
    result = posixpath.relpath(target.rstrip('/'), start)
    return result + ('/' if target.endswith('/') else '')

def disk_path(url):
    return OUT / url.lstrip('/') / 'index.html' if url.endswith('/') else OUT / url.lstrip('/')

def esc(value):
    return html.escape(str(value), quote=True)

def state(value, yes='Yes', no='No'):
    return yes if value is True else no if value is False else 'Decision / lifecycle check'

def html_page(url, title, head, content):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | STUDIO-5864 QA</title>
{head}
<link rel="stylesheet" href="{relative(url, '/assets/site.css')}">
</head>
<body class="fixture-body">
<header class="fixture-brand"><span class="brand-mark">S/</span><span>SEARCHSTAX <b>QA LAB</b></span><span class="ticket-label">STUDIO-5864</span></header>
<main class="fixture-main">{content}</main>
<footer class="fixture-footer">Isolated crawl fixture. No navigation, sitemap, canonical or alternate discovery links are added.</footer>
</body></html>
'''

def build(config):
    for directory in ('cases', 'suites'):
        shutil.rmtree(OUT / directory, ignore_errors=True)
    for p in (OUT / 'assets', QA):
        p.mkdir(parents=True, exist_ok=True)
    cases = make_cases(config)
    headers_map = {}
    pages = []
    all_case_data = []
    phase = config['phase']
    version = {'baseline':'V1','restricted':'V2','restored':'V3'}[phase]
    base_path = config['base_path'].rstrip('/')

    def record_page(url, content, *, cid, role, headers=None, links=None, marker='', kind='html'):
        write(disk_path(url), content)
        hs = headers or []
        if hs:
            headers_map[url] = hs
            if url.endswith('/'):
                headers_map[url + 'index.html'] = hs
        pages.append({'url':url,'case_id':cid,'role':role,'headers':hs,
                      'links':links or [],'marker':marker,'kind':kind})

    for c in cases:
        targets = {t['slug']:t for t in c['targets']}
        parent = c['parent']
        marker = 'QA5864' + c['id'] + 'P' + (version if c['group']=='Lifecycle' else '')
        c['marker'] = marker
        c['phase_version'] = version if c['group']=='Lifecycle' else None
        def anchors(from_url, link_specs):
            snippets=[]
            resolved=[]
            for i, link in enumerate(link_specs):
                target = targets[link['target']]['url']
                fragment = ('#' + link['fragment']) if link.get('fragment') else ''
                rel_attr = '' if link.get('rel') is None else ' rel="' + esc(link['rel']) + '"'
                href = relative(from_url, target) + fragment
                snippets.append(f'<a class="test-link" href="{esc(href)}"{rel_attr}>Occurrence {i+1}: {esc(link["target"])} <span aria-hidden="true">&rarr;</span></a>')
                resolved.append({'url':target,'rel':link.get('rel'),'fragment':link.get('fragment','')})
            return '\n'.join(snippets), resolved
        link_html, parent_links = anchors(parent,c['links'])
        header_display = '\n'.join(n+': '+v for n,v in c['headers']) or '(No custom robots response header for this page)'
        source_display = c['raw_head'] or '(No robots meta tag in the head)'
        content = f'''<div class="eyebrow">{esc(c['group'])} / {c['id']}</div>
<h1>{esc(c['title'])}</h1>
<p class="lead">A deterministic fixture for STUDIO-5864. Use this scenario, not the dashboard, as your crawl Start URL.</p>
<section class="panel"><span class="field-label">SCENARIO CRAWL START URL</span><pre><code>{esc(base_path+c["seed"])}</code></pre><p class="muted">Use your deployed hostname plus this path. Do not add child URLs as separate seeds.</p></section>
<div class="fixture-chips"><span class="chip">{esc(c['gate'])}</span><span class="chip">Parent page</span>{'<span class="chip">'+version+'</span>' if c['group']=='Lifecycle' else ''}</div>
<section class="token-card"><span class="eyebrow">Unique content marker</span><strong>{marker}</strong><p>This marker exists in this fixture only. Query it in the index and inspect the document URL.</p></section>
<div class="fixture-grid"><section class="panel"><h2>HTML head fixture</h2><pre><code>{esc(source_display)}</code></pre></section>
<section class="panel"><h2>Required HTTP response</h2><pre><code>{esc(header_display)}</code></pre><p class="muted">Header text shown here is documentation, not a response header. Verify the real GET response.</p></section></div>
<section class="panel"><h2>Expected behavior</h2><p>Index this parent: <strong>{state(c['index'])}</strong>. Follow page links before link-level filtering: <strong>{state(c['follow'])}</strong>.</p>
<p>{esc(c['note'])}</p>{'<p class="warning-text">This parent is blocked in robots.txt. Expectations above apply only when Ignore robots.txt is ON. OFF: do not fetch the parent.</p>' if c['robots_blocked'] else ''}
{ '<p class="warning-text">This is not an unconditional pass/fail case. Resolve its prerequisites or product decision first.</p>' if c['gate']!='Ready' else ''}
{ '<p class="warning-text">PROPOSED ONLY: parent index = '+state(c['proposed']['parent_index'])+'; child eligible = '+state(c['proposed']['child_eligible'])+'. Confirm the product policy before grading.</p>' if c.get('proposed') else ''}</section>
<section class="panel"><h2>Actual crawl graph links</h2><p class="muted">Only the anchors below create discovery paths for this fixture.</p><div class="test-links">{link_html}</div></section>
{c['raw_body']}
'''
        record_page(parent,html_page(parent,c['title'],c['raw_head'],content),cid=c['id'],role='parent',headers=c['headers'],links=parent_links,marker=marker)
        if c['robots_blocked']:
            seed=c['seed']
            entry_content=f'''<div class="eyebrow">robots.txt switch / {c['id']}</div><h1>Allowed entry for {c['id']}</h1><p>This seed is allowed by robots.txt. Its only link discovers a blocked parent. Children of that parent live outside the blocked path.</p><a class="test-link" href="{relative(seed,parent)}">Discover the blocked parent</a>'''
            record_page(seed, html_page(seed,c['id']+' allowed entry','',entry_content),cid=c['id'],role='entry',links=[{'url':parent,'rel':None}])
        for t in c['targets']:
            token='QA5864'+c['id']+re.sub('[^A-Za-z0-9]','',t['slug']).upper()
            t['marker']=token
            if t.get('type','html')=='text':
                text=f"STUDIO-5864 text fixture\nCase: {c['id']}\nRole: {t['slug']}\nUnique marker: {token}\nThis is a plain-text extraction control. Header-only indexing restrictions apply independently of document format.\n"
                record_page(t['url'],text,cid=c['id'],role='target',headers=t['headers'],marker=token,kind='text')
            else:
                target_meta='\n'.join(f'<meta name="{esc(n)}" content="{esc(v)}">' for n,v in t.get('meta',[]))
                target_anchor_html,target_links=anchors(t['url'],c.get('target_links',{}).get(t['slug'],[]))
                content=f'''<div class="eyebrow">{c['id']} / ISOLATED TARGET</div><h1>{esc(t['slug'].replace('-',' ').title())}</h1><p class="lead">This target belongs only to case {c['id']}. It is not listed in a seed suite or sitemap.</p><section class="token-card"><span class="eyebrow">Unique content marker</span><strong>{token}</strong></section><section class="panel"><h2>Fixture content</h2><p>A static target used to distinguish page processing, link discovery, queue eligibility and indexing. No return links or shared navigation exist.</p>{target_anchor_html}</section>'''
                record_page(t['url'],html_page(t['url'],c['id']+' '+t['slug'],target_meta,content),cid=c['id'],role='target',headers=t['headers'],links=target_links,marker=token)
        c['expected_on']={'parent_fetch':True,'parent_index':c['index'],'targets':[{'url':t['url'],'fetch':t['fetch'],'index':t['index'],'marker':t['marker']} for t in c['targets']]}
        c['expected_off']=({'parent_fetch':False,'parent_index':False,'targets':[{'url':t['url'],'fetch':False,'index':False,'marker':t['marker']} for t in c['targets']]} if c['robots_blocked'] else c['expected_on'])
        all_case_data.append(c)

    suite_specs=[
        ('core','Core regression','No response-header dependency. Generic meta, unrelated bots and link rules.',lambda c:c['gate']=='Ready' and c['group'] in ('HTML meta','Bot targeting','Link rules')),
        ('meta','HTML meta','Independent noindex/nofollow behavior and parsing edge cases.',lambda c:c['group']=='HTML meta' and c['gate']=='Ready'),
        ('links','Link rules','Occurrence-level suppression and alternate-path controls.',lambda c:c['group']=='Link rules'),
        ('headers','HTTP headers','Real response headers must be configured before this run.',lambda c:c['group']=='HTTP headers' and c['gate']=='Ready'),
        ('robots','robots.txt switch','Run twice with fresh state: Ignore robots.txt OFF, then ON.',lambda c:c['group']=='robots.txt switch'),
        ('bots','Confirmed-token tests','Requires the exact supported SearchStax meta-name mapping.',lambda c:c['group']=='Bot targeting' and 'bot-token' in c['requires']),
        ('decisions','Contract decisions','Exploratory only until the behavior is agreed.',lambda c:c['gate']=='Confirm'),
    ]
    suites=[]
    for slug,title,description,predicate in suite_specs:
        members=[c for c in cases if predicate(c)]
        url='/suites/'+slug+'/'
        anchors_html='\n'.join(f'<a class="suite-link" href="{relative(url,c["seed"])}"><b>{c["id"]}</b> {esc(c["title"])}</a>' for c in members)
        content=f'<div class="eyebrow">CRAWL SEED SUITE</div><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p><p>Only case-entry URLs are listed. Targets are deliberately not exposed here. Include both /suites/ and /cases/ in the crawler scope, not this seed directory alone.</p><section class="panel suite-links">{anchors_html}</section>'
        record_page(url,html_page(url,title,'',content),cid='',role='suite',links=[{'url':c['seed'],'rel':None} for c in members])
        suites.append(dict(slug=slug,title=title,description=description,url=url,count=len(members),case_ids=[c['id'] for c in members]))

    robots='''# STUDIO-5864 QA fixtures. Serve this file at the HOST ROOT /robots.txt.
# A /repository/robots.txt file on a project site does not control the host.
# No Sitemap declaration: target isolation is intentional.
User-agent: *
'''
    for c in cases:
        if c['robots_blocked']:
            robots+='Disallow: '+base_path+c['parent']+'\n'
    write(OUT/'robots.txt',robots)
    write(QA/'robots-host-root-example.txt',robots)
    write(OUT/'.nojekyll','')
    write(OUT/'404.html',html_page('/404.html','Not a fixture','<meta name="robots" content="noindex,nofollow">','<h1>Fixture not found</h1><p>This path does not belong to the generated test graph. Verify the copied seed URL. No catch-all rewrite is configured.</p>'))

    # Local server keeps duplicate field lines; CDN rules combine same-name values.
    write(QA/'http-headers.json',json.dumps(headers_map,indent=2)+'\n')
    def combined_headers(pairs):
        grouped={}
        for name,value in pairs:
            key=name.lower()
            grouped.setdefault(key,[name,[]])[1].append(value)
        return [(name,', '.join(values)) for name,values in grouped.values()]
    netlify='''# Deploy docs/ as the publish directory. These are real host HTTP rules.
# Physical duplicate header fields may be combined by the CDN.
/*
  Cache-Control: no-store, max-age=0
'''
    render='''# Import this repository using New > Blueprint so these header rules apply.
services:
  - type: web
    name: studio-5864-robots-qa
    runtime: static
    buildCommand: echo Static fixtures are prebuilt
    staticPublishPath: ./docs
    headers:
      - path: /*
        name: Cache-Control
        value: no-store, max-age=0
'''
    rules=[]
    for url,pairs in sorted(headers_map.items()):
        deployed=base_path+url
        netlify+='\n'+deployed+'\n'
        for name,value in combined_headers(pairs):
            netlify+='  '+name+': '+value+'\n'
            render+=f'      - path: {json.dumps(deployed)}\n        name: {json.dumps(name)}\n        value: {json.dumps(value)}\n'
            rules.append({'Path':deployed,'Name':name,'Value':value})
    write(OUT/'_headers',netlify)
    write(ROOT/'hosting/render-static.yaml',render)
    write(ROOT/'render.yaml', '''# Default: a FREE web service serving static fixtures with real repeated headers.
# Deploy a NEW service; this is intentionally not the old static-site definition.
services:
  - type: web
    name: studio-5864-robots-qa-v2
    runtime: python
    plan: free
    buildCommand: python3 tools/build.py
    startCommand: python3 tools/serve.py --bind 0.0.0.0
    healthCheckPath: /healthz
    envVars:
      - key: PYTHONUNBUFFERED
        value: "1"
''')
    write(ROOT/'netlify.toml','[build]\n  publish = "docs"\n  command = "echo Static fixtures are prebuilt"\n')
    with (QA/'render-header-rules.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=['Path','Name','Value']);writer.writeheader();writer.writerows(rules)

    manifest={'schema_version':2,'site_version':config.get('site_version','2.0.0'),'ticket':TICKET,'build_phase':phase,'version':version,
              'bot_meta_name':config['bot_meta_name'],'bot_mapping_confirmed':config['bot_mapping_confirmed'],
              'crawler_http_user_agent':config['crawler_http_user_agent'],'base_path':base_path,
              'case_count':len(cases),'fixture_url_count':len(pages),'gate_counts':dict(Counter(c['gate'] for c in cases)),
              'warning':'All actual crawler results are Not run. Fixture verification is not SearchStax QA sign-off.',
              'suites':suites,'cases':all_case_data,'pages':pages}
    write(OUT/'assets/manifest.json',json.dumps(manifest,indent=2)+'\n')
    write(QA/'expected-results.json',json.dumps(manifest,indent=2)+'\n')

    # TestRail single-row-per-case import. No actual results are invented.
    fields=['Title','Section','Type','Priority','Preconditions','Steps','Expected Result','References','Actual Result']
    rows=[]
    for c in cases:
        pre='Use this scenario URL as the sole Start URL, never the dashboard or a suite. Dedicated non-production index; fresh crawl queue/index for each independent run. Disable sitemap/import discovery. Allow all /cases/ paths and seed /suites/ paths; depth >= 5; item limit >= 500. Wait for the previous run to finish. Use the published site base URL. '
        pre+='Gate: '+c['gate']+'. Requirements: '+(', '.join(c['requires']) or 'none')+'. '
        if c['requires']:
            pre+='Verify hosting/token/parser prerequisites before assigning a result. '
        steps=f"1. Copy start URL: {{BASE_URL}}{c['seed']}. For isolated execution, do not seed any target directly.\n2. Inspect the final GET response and original HTML; confirm the active fixture and record the actual crawler user-agent.\n3. Run a full crawl; record environment, app ID, crawl definition ID, crawl run ID, settings and timestamps.\n4. Check parent processing/indexing and every target's discovery/queue/index evidence; search unique markers and inspect exact document URLs.\n5. Repeat with Ignore robots.txt toggled in a clean run; repeat the same setting once to check stability and duplicate documents."
        expected=f"Parent marker: {c['marker']}. With Ignore robots.txt ON: parent fetched = Yes; indexed = {state(c['index'])}. "
        expected+='Targets: '+'; '.join(t['url']+': fetched/queue-eligible='+state(t['fetch'])+', indexed='+state(t['index'])+', marker='+t['marker'] for t in c['targets'])+'. '
        expected+=('With Ignore robots.txt OFF: blocked parent not fetched; targets not discovered from this case.' if c['robots_blocked'] else 'With Ignore robots.txt OFF: the same page-level behavior applies.')
        expected+=(' Proposed only: parent index='+state(c['proposed']['parent_index'])+'; child eligible='+state(c['proposed']['child_eligible'])+'. Confirm policy before pass/fail.' if c.get('proposed') else '')
        expected+=' '+c['note']+' Always distinguish noindex (processing permitted, no add/update) from nofollow (no enqueue from this occurrence). HTTP retries do not imply duplicate index documents.'
        if c['group']=='Lifecycle':
            pre='Dedicated test index retained across the three lifecycle phases; no independent target discovery. '+pre.replace('fresh crawl queue/index for each independent run.','retain indexed V1 for this same-URL lifecycle test.')
            steps=f"1. Build baseline: python3 tools/build.py --phase baseline. Deploy and force-crawl {{BASE_URL}}{c['seed']}; verify V1/old-child as applicable.\n2. Build restricted: python3 tools/build.py --phase restricted. Deploy the changed files AND header rules, then verify the live GET response before crawling.\n3. Force-crawl the SAME URL without clearing the existing index. Check V2 add/update suppression for noindex or new-child queue suppression for nofollow.\n4. Record retained/deleted legacy content separately; do not invent a deletion requirement.\n5. Build restored: python3 tools/build.py --phase restored. Deploy files AND header rules and force-crawl the SAME URL.\n6. Verify V3/new-child as applicable, then repeat for stability. Record real evidence for every phase."
            expected=c['note']+' Actual results remain Not run until executed in SearchStax.'
        rows.append(dict(zip(fields,[c['id']+' - '+c['title'],c['group'],'Functional',c['priority'],pre,steps,expected,TICKET+('\nhttps://html.spec.whatwg.org/multipage/links.html' if c['id']=='L15' else ''),'Not run'])))
    for dest in (QA/'testrail-cases.csv',OUT/'assets/testrail-cases.csv'):
        with dest.open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    write(QA/'results-template.json',json.dumps({'ticket':'STUDIO-5864','run_id':'','environment':'','app_id':'','crawl_definition_id':'','crawl_run_id':'','ignore_robots_txt':False,'phase':phase,'records':[{'case_id':c['id'],'result':'Not run','actual':'','evidence':''} for c in cases]},indent=2)+'\n')
    # Scenario-first reference files are regenerated with the same source data.
    scenario_fields=['Case ID','Scenario','Start URL','Parent marker','Readiness']
    with (QA/'scenario-start-urls.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=scenario_fields);w.writeheader()
        for c in cases:
            w.writerow(dict(zip(scenario_fields,[c['id'],c['title'],'{BASE_URL}'+c['seed'],c['marker'],c['gate']])))
    new_header_rows=[r for r in rows if re.match(r'H(1[5-9]|2[0-9]|3[0-4]) - ',r['Title'])]
    with (QA/'header-precedence-cases.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(new_header_rows)
    reference=[
        '# HTTP header precedence and repeated-field tests - v2',
        '',
        'Use each individual scenario Start URL. Prepend your deployed hostname. Never use the dashboard or a suite as the Start URL.',
        '',
        'The default matching identity is `SearchStax Crawler`. All header strings below are actual server output, not HTML meta substitutes. The origin sends multiple fields separately, in the listed order. Confirm public delivery with `tools/verify.py BASE_URL --require-repeated` before grading physical repeated-header cases.',
        '',
        '## Acceptance versus proposal',
        '',
        'Ready cases have authored expectations. For Confirm cases, the expected result is a product decision, and any candidate result below is explicitly PROPOSED. The ticket describes specific-over-generic precedence for HTML meta; it does not fully define header scope/source aggregation. Confirm those rules in Jira before assigning pass/fail. This suite never computes a fake crawler result.',
        '',
        'Proposed general policy: matching-specific over generic when both dimensions are explicit; ignore unrelated scopes; aggregate independent same-scope restrictions; resolve same-scope conflicts consistently. H29 leaves the child outcome open because whole-scope replacement and per-dimension override differ. H33/H34 leave cross-source outcomes open.',
        '',
        'H08 is a text extraction control pair: its parent has no header; the allowed text may index, but the restricted text must not index. Establish text parser support before grading.',
        '',
        '## Cases',
        '',
        '| Case / Start path | Actual header field(s), top to bottom | Meta input | Parent index / child eligible | Readiness |',
        '|---|---|---|---|---|'
    ]
    for c in cases:
        if c['group']!='HTTP headers': continue
        hs='<br>'.join('`'+n+': '+(v if v else '(empty value)')+'`' for n,v in c['headers']) or 'None on parent; see target fixtures'
        meta_text=c['raw_head'].replace('<','&lt;').replace('>','&gt;') or 'None'
        proposal=c.get('proposed')
        outcome=('PROPOSED: '+state(proposal['parent_index'])+' / '+state(proposal['child_eligible'])) if proposal else state(c['index'])+' / '+state(c['follow'])
        reference.append('| '+c['id']+' `'+c['seed']+'` | '+hs+' | '+meta_text+' | '+outcome+' | '+c['gate']+' |')
    reference.extend(['','## Notes for H15-H34',''])
    for c in cases:
        if c.get('added_in')=='2.0.0': reference.append('**'+c['id']+'** - '+c['note']+'\n')
    reference.extend(['## Execution steps','','1. Inspect the final GET response and confirm the exact field values/count/order. Keep verifier/browser requests outside the crawler evidence time window.','2. Start a fresh dedicated crawl from only the scenario URL, with its child path in scope. Capture the actual HTTP User-Agent.','3. Verify parent processing and index add/update separately; noindex must not be misread as a crawl prohibition.','4. Inspect the child queue provenance and unique document marker. Missing search results alone do not prove nofollow.','5. Compare order-reversal pairs in separate clean runs; repeat selected cases with Ignore robots.txt OFF and ON. Page-level outcomes must not change when robots.txt does not block the page.','6. Keep all actual results Not run until executed. Confirm cases require an agreed product rule and evidence.','','Source: '+TICKET+' and the user-provided v2 change request. No current Jira comment contents were assumed.',''])
    write(QA/'HEADER-PRECEDENCE.md','\n'.join(reference))
    print(json.dumps({'cases':len(cases),'fixture_urls':len(pages),'gates':manifest['gate_counts'],'phase':phase},indent=2))
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['baseline','restricted','restored'])
    parser.add_argument('--bot-name',help='Supported robots meta name; quote names containing spaces, e.g. "SearchStax Crawler"')
    parser.add_argument('--confirm-bot-token',action='store_true')
    parser.add_argument('--user-agent',help='Recorded actual crawler HTTP User-Agent, documentation only')
    parser.add_argument('--base-path',help='URL path prefix such as /repo; empty for root hosting')
    args=parser.parse_args()
    config=json.loads((ROOT/'config.json').read_text())
    if args.phase: config['phase']=args.phase
    if args.bot_name:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9 _./-]{0,79}',args.bot_name):
            parser.error('Use a supported bot name without control characters, quotes or colons. Spaces are allowed, for example SearchStax Crawler.')
        config['bot_meta_name']=args.bot_name
        config['bot_mapping_confirmed']=False
    if args.confirm_bot_token: config['bot_mapping_confirmed']=True
    if args.user_agent: config['crawler_http_user_agent']=args.user_agent
    if args.base_path is not None:
        p=args.base_path.rstrip('/')
        if p and (not p.startswith('/') or '..' in p or not re.fullmatch(r'/[A-Za-z0-9_/-]+',p)):
            parser.error('base-path must be an absolute URL path without dot segments, e.g. /robots-qa')
        config['base_path']=p
    write(ROOT/'config.json',json.dumps(config,indent=2)+'\n')
    build(config)

if __name__=='__main__': main()
