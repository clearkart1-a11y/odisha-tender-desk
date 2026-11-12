"""Static, SEO-first website generator for Odisha Tender Desk.
Outputs ./_site/ (deployable to any static host: Netlify, Cloudflare Pages, Vercel, S3).
Public pages: home, tenders (one per open tender), districts, departments, work types, guides, pricing, sign-up.
Bidder profiles are NOT generated as public pages (sign-in only, noindex)."""
import json, re, os, html, shutil, gzip, statistics as st, collections as C, datetime as DT, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import district, material
from seg import seg

def load(name):
    with gzip.open(os.path.join(ROOT, 'data', name), 'rt', encoding='utf-8') as f: return json.load(f)

SITE_URL = os.environ.get('SITE_URL', 'https://www.odishatenderdesk.in').rstrip('/')   # placeholder domain, set before deploy
FORM_ENDPOINT = os.environ.get('FORM_ENDPOINT', '')   # e.g. a Formspree / Netlify Forms / Google Apps Script URL
BRAND = 'Odisha Tender Desk'
TODAY = (DT.datetime.utcnow() + DT.timedelta(hours=5, minutes=30)).date()  # IST
STALE_DAYS = 60   # closed tenders older than this: noindex, out of sitemap
OUT = os.environ.get('OUT', os.path.join(ROOT, '_site'))
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)

def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')
    return s or 'na'

def inr(v):
    if not v: return '–'
    if v >= 1e7: return f'₹{v/1e7:,.2f} Cr'
    if v >= 1e5: return f'₹{v/1e5:,.1f} L'
    return f'₹{v:,.0f}'

def pct(x, d=1):
    if x is None: return '–'
    return ('+' if x > 0 else '−' if x < 0 else '') + f'{abs(x):.{d}f}%'

def num(x):
    try: return float(re.sub(r'[^\d.]', '', x or '') or 0)
    except: return 0.0

def pdate(s):
    try: return DT.datetime.strptime((s or '')[:11], '%d-%b-%Y').date()
    except: return None

# ---------------------------------------------------------------- data
A = {a['id']: a for a in load('active.json.gz')}
BOQ = load('boq_summary.json.gz')
MIX = {r['id']: r for r in load('boq_mix.json.gz')}
T = [t for t in load('results_2026.json.gz') if t.get('l1') is not None and not t.get('bad') and t.get('era') == '2026']
td = district.build([(t['loc'], t['pin'], ' '.join([t['circle'] or '', t['div'] or '', t['dept'] or '', t['title'] or ''])) for t in T])
for t, d in zip(T, td):
    t['district'] = d or ''; t['seg'] = seg(t['dept']); t['mat'] = material.classify(t['title'], t['cat'])
OPEN = list(A.values())
od = district.build([(a.get('loc'), a.get('pin'), (a.get('org') or '') + ' ' + (a.get('title') or '')) for a in OPEN])
for a, d in zip(OPEN, od):
    a['district'] = d or ''; a['seg'] = seg(a.get('_org') or ''); a['est'] = num(a.get('val'))
    cd = pdate(a.get('close')) or TODAY
    a['closed'] = cd < TODAY; a['stale'] = (TODAY - cd).days > STALE_DAYS
    a['pubd'] = pdate(a.get('pub'))
    a['url'] = '/tenders/' + slug(a['id']) + '/'
    m = MIX.get(a['id']); a['wt'] = m['cls'] if m else None
    a['est_boq'] = False
    if not a['est'] and m and m.get('boq_total'): a['est'] = float(m['boq_total']); a['est_boq'] = True

def market(rows):
    if not rows: return None
    l = [t['l1'] for t in rows]
    return dict(n=len(rows), med=st.median(l), par=sum(x > -1 for x in l) / len(l), deep=sum(x < -15 for x in l) / len(l),
                bid=st.mean(t['npriced'] for t in rows))

DIST = sorted({a['district'] for a in OPEN if a['district']} | {t['district'] for t in T if t['district']})
SEGS = sorted({a['seg'] for a in OPEN} | {t['seg'] for t in T})
WTS = ['Concrete structure (CC road/bridge/canal)', 'Building', 'Pipeline / lift irrigation', 'Bituminous road', 'Earth & gravel/WBM road', 'Mixed']
WT_SLUG = {w: slug(w.split('(')[0]) for w in WTS}
COL = {'Cement concrete': '#7f8c8d', 'Steel': '#4a6fa5', 'Bitumen / road surfacing': '#3b3b3b', 'Stone / aggregate': '#a1887f', 'Earthwork': '#c49a6c',
       'Pipes & fittings': '#2e8b8b', 'Electrical': '#d4a72c', 'Finishing': '#9b7bb5', 'Brick / masonry': '#b5624b', 'Other': '#c7cfcc', 'Routine maintenance': '#8fb39a', 'Formwork': '#999'}

# ---------------------------------------------------------------- layout
CSS = open(HERE + '/site.css').read()
PAGES = []  # (path, priority, changefreq)

def page(path, title, desc, body, crumbs=(), jsonld=None, prio=0.5, freq='weekly', noindex=False, lastmod=None):
    url = SITE_URL + path
    bc = [('Home', '/')] + list(crumbs)
    bl = {"@context": "https://schema.org", "@type": "BreadcrumbList",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE_URL + u} for i, (n, u) in enumerate(bc)]}
    lds = [bl] + (jsonld or [])
    crumb_html = '' if path == '/' else '<nav class="crumbs" aria-label="Breadcrumb">' + ' / '.join(
        f'<a href="{u}">{E(n)}</a>' for n, u in bc[:-1]) + f' / <span>{E(bc[-1][0])}</span></nav>'
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
{'<meta name="robots" content="noindex,nofollow">' if noindex else '<meta name="robots" content="index,follow">'}
<meta property="og:type" content="website"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="{BRAND}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"><link rel="stylesheet" href="/assets/site.css">
{''.join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in lds)}
</head><body>
<header class="top"><div class="wrap topbar"><a class="logo" href="/">{BRAND}</a>
<nav aria-label="Main"><a href="/tenders/">Tenders</a><a href="/districts/">Districts</a><a href="/departments/">Departments</a><a href="/guides/">Guides</a><a href="/pricing/">Pricing</a><a class="btn sm" href="/signup/">Free sign-up</a></nav></div></header>
<main class="wrap">{crumb_html}{body}</main>
<footer><div class="wrap"><div class="fcols"><div><b>{BRAND}</b><p>Tender intelligence for Odisha civil contractors, built on public results from tendersodisha.gov.in.</p></div>
<div><b>Explore</b><p><a href="/tenders/">Open tenders</a><br><a href="/districts/">Districts</a><br><a href="/departments/">Departments</a><br><a href="/work-types/">Work types</a></p></div>
<div><b>Learn</b><p><a href="/guides/">Guides</a><br><a href="/pricing/">Pricing</a><br><a href="/about/">About the data</a></p></div></div>
<p class="fine">Data from tendersodisha.gov.in public pages; always check the official notice before bidding. Not affiliated with the Government of Odisha. We support independent pricing only: agreeing prices or turns with other bidders is bid rigging under the Competition Act, 2002.</p></div></footer>
</body></html>'''
    fp = OUT + path + 'index.html'
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'w').write(doc)
    if not noindex: PAGES.append((path, prio, freq, lastmod or TODAY))

def mixbar(m, top=6):
    items = sorted(m.items(), key=lambda x: -x[1])[:top]
    return ('<div class="bar">' + ''.join(f'<span style="width:{v*100:.1f}%;background:{COL.get(k,"#bbb")}" title="{E(k)} {v*100:.0f}%"></span>' for k, v in items) + '</div>'
            '<ul class="legend">' + ''.join(f'<li><i style="background:{COL.get(k,"#bbb")}"></i>{E(k)} <b>{v*100:.0f}%</b></li>' for k, v in items) + '</ul>')

def mkt_block(m, label):
    if not m or m['n'] < 5:
        return f'<p class="muted">Not enough 2026 results in {E(label)} yet.</p>'
    hint = ('Most are won at par and decided by draw.' if m['par'] >= .4 else
            'Expect a fight on price.' if m['deep'] >= .5 else 'Discounts vary widely.')
    return (f'<p class="say"><b class="big">{pct(m["med"])}</b> is the typical winning bid here '
            f'<span class="muted">({m["n"]:,} results in 2026, about {m["bid"]:.0f} bidders each).</span> {hint}</p>')

def tender_rows(rows, limit=400, fold=12, show_dist=True):
    rows = sorted(rows, key=lambda a: (a['closed'], pdate(a.get('close')) or DT.date(2100, 1, 1)))
    rows = ([a for a in rows if not a['closed']] or rows)[:limit]
    def tr(a):
        return (f'<tr><td><a href="{a["url"]}">{E(a["title"][:95])}{"…" if len(a["title"])>95 else ""}</a></td>'
                + (f'<td>{E(a["district"] or "–")}</td>' if show_dist else '') +
                f'<td class="n">{inr(a["est"])}</td><td class="n">{E((a.get("close") or "")[:6])}</td></tr>')
    head = '<thead><tr><th>Work</th>' + ('<th>District</th>' if show_dist else '') + '<th class="n">Estimate</th><th class="n">Closes</th></tr></thead>'
    tbl = lambda rs: '<div class="tbl"><table class="list">' + head + '<tbody>' + ''.join(tr(a) for a in rs) + '</tbody></table></div>'
    if len(rows) <= fold + 3: return tbl(rows)
    return tbl(rows[:fold]) + f'<details class="more"><summary>Show all {len(rows)} tenders</summary>{tbl(rows[fold:])}</details>'

def cta(text='See who usually wins here and what they bid.'):
    return f'<p class="cta-line">{E(text)} <a href="/signup/">Get your free profile →</a></p>'

# ---------------------------------------------------------------- build
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT + '/assets')
open(OUT + '/assets/site.css', 'w').write(CSS)
mk_all = market(T)

# tenders
for a in OPEN:
    b = BOQ.get(a['id']); m = MIX.get(a['id'])
    seg_m = market([t for t in T if t['seg'] == a['seg'] and (not a['district'] or t['district'] == a['district'])])
    seg_only = market([t for t in T if t['seg'] == a['seg']])
    facts = [('Tender ID', a['id']), ('Reference', a.get('ref')), ('Organisation', (a.get('org') or '').replace('||', ' › ')), ('Estimate (tender value)', inr(a['est'])),
             ('Category', a.get('pc')), ('Location', a.get('loc')), ('District', a['district'] or '–'), ('Published', a.get('pub')), ('Bid submission closes', a.get('close')),
             ('Bid opening', a.get('open')), ('EMD', ('₹' + a['emd']) if a.get('emd') and a['emd'] != 'NA' else '–'), ('Contractor class', a.get('cls')), ('Form of contract', a.get('form'))]
    boq_html = ''
    if b and m:
        items = b['top']; k80 = b['k80']
        boq_html = (f'<section><h2>What the BOQ says</h2><p>Work type from the BOQ: <b>{E(m["cls"])}</b>. {b['n']} priced items; '
                    f'<b>{k80}</b> of them make up 80% of the value.</p>{mixbar(m["mix"])}'
                    '<details class="more"><summary>Largest BOQ items</summary><div class="tbl"><table><thead><tr><th>Item</th><th class="n">Qty</th><th>Unit</th><th class="n">Rate</th><th class="n">Amount</th></tr></thead><tbody>' +
                    ''.join(f'<tr><td>{E(i[1][:180])}</td><td class="n">{i[2]:,.2f}</td><td>{E(i[3])}</td><td class="n">₹{i[4]:,.2f}</td><td class="n">{inr(i[5])}</td></tr>' for i in items[:6]) +
                    '</tbody></table></div><p class="muted">Rates are the department’s estimated rates from the published BOQ, not market prices.</p></details></section>')
    else:
        boq_html = ''
    loc_label = f'{a["seg"]}' + (f', {a["district"]}' if a['district'] else '')
    emd = ('₹' + a['emd']) if a.get('emd') and a['emd'] != 'NA' else '–'
    key = [('Estimate (BOQ total)' if a['est_boq'] else 'Estimate', inr(a['est'])), ('Closes' if not a['closed'] else 'Closed', (a.get('close') or '')[:11]), ('District', a['district'] or a.get('loc') or '–'), ('EMD', emd)]
    body = (f'<h1 class="t">{E(a["title"])}</h1><p class="sub">{E(a["seg"])} · Tender {E(a["id"])}</p>'
            '<div class="keys">' + ''.join(f'<div><span>{k}</span><b>{E(v)}</b></div>' for k, v in key) + '</div>'
            f'<section><h2>How this market bids</h2>{mkt_block(seg_m if seg_m and seg_m["n"]>=5 else seg_only, loc_label)}{cta()}</section>'
            + boq_html +
            '<details class="more"><summary>All tender details</summary><dl class="facts">' + ''.join(f'<dt>{E(k)}</dt><dd>{E(v)}</dd>' for k, v in facts if v) + '</dl>'
            '<p class="muted">Download documents and bid only on <a href="https://tendersodisha.gov.in/nicgep/app" rel="nofollow noopener">tendersodisha.gov.in</a>.</p></details>' +
            f'<p class="links">More: <a href="/districts/{slug(a["district"])}/">{E(a["district"])} tenders</a> · <a href="/departments/{slug(a["seg"])}/">{E(a["seg"])}</a>'
            + (f' · <a href="/work-types/{WT_SLUG[m["cls"]]}/">{E(m["cls"])}</a>' if m and m['cls'] in WT_SLUG else '') + '</p>')
    desc = f'{a["title"][:110]} – {a["seg"]}, {a["district"] or a.get("loc")}. Estimate {inr(a["est"])}, closes {(a.get("close") or "")[:11]}. BOQ breakdown and how this market bids.'
    page(a['url'], f'{a["title"][:60]} | Tender {a["id"]}', desc, body,
         crumbs=[('Tenders', '/tenders/'), (a['id'], a['url'])], prio=0.6 if not a['closed'] else 0.3, freq='daily' if not a['closed'] else 'monthly', noindex=a['stale'], lastmod=min(a['pubd'] or TODAY, TODAY))

# tenders index + search json
openrows = [a for a in OPEN if not a['closed']]
idx = [[a['id'], a['title'][:120], a['seg'], a['district'], round(a['est']), (a.get('close') or '')[:11], a['wt'] or '', a['url'], a['closed']] for a in OPEN]
open(OUT + '/assets/tenders.json', 'w').write(json.dumps(idx, separators=(',', ':'), ensure_ascii=False))
body = (f'<h1>Open tenders</h1><p class="lede">{len(openrows):,} civil tenders open for bidding in Odisha. Search or filter, then open one to see its BOQ and how that market bids.</p>'
        '<div class="filters"><input id="q" type="search" placeholder="Search by work, tender ID or place" aria-label="Search tenders">'
        '<select id="fd" aria-label="District"><option value="">All districts</option>' + ''.join(f'<option>{E(d)}</option>' for d in DIST) + '</select>'
        '<select id="fs" aria-label="Department"><option value="">All departments</option>' + ''.join(f'<option>{E(s)}</option>' for s in SEGS) + '</select></div>'
        '<div id="list">' + tender_rows(OPEN, 80, fold=999) + '</div><p class="muted" id="cnt"></p>'
        '<script>(async()=>{const L=await (await fetch("/assets/tenders.json")).json();const P=new URLSearchParams(location.search);const q=document.getElementById("q"),fd=document.getElementById("fd"),fs=document.getElementById("fs");'
        'const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;"}[c]));const inr=v=>v>=1e7?"₹"+(v/1e7).toFixed(2)+" Cr":v>=1e5?"₹"+(v/1e5).toFixed(1)+" L":"₹"+v.toLocaleString("en-IN");'
        'function r(){const s=q.value.trim().toLowerCase();const R=L.filter(x=>(!x[8]||s)&&(!fd.value||x[3]===fd.value)&&(!fs.value||x[2]===fs.value)&&(!s||(x[0]+" "+x[1]+" "+x[3]).toLowerCase().includes(s))).sort((a,b)=>a[8]-b[8]);'
        'document.getElementById("list").innerHTML=\'<div class="tbl"><table class="list"><thead><tr><th>Work</th><th>District</th><th class="n">Estimate</th><th class="n">Closes</th></tr></thead><tbody>\'+R.slice(0,150).map(x=>`<tr><td><a href="${x[7]}">${esc(x[1])}</a>${x[8]?" <span class=chip>closed</span>":""}</td><td>${esc(x[3]||"–")}</td><td class="n">${inr(x[4])}</td><td class="n">${esc(x[5].slice(0,6))}</td></tr>`).join("")+"</tbody></table></div>";'
        'document.getElementById("cnt").textContent=R.length+" tenders match"+(R.length>150?"; showing 150":"");}[q,fd,fs].forEach(e=>e.addEventListener("input",r));if(P.get("q")){q.value=P.get("q");r();}})();</script>')
page('/tenders/', 'Open Odisha Civil Tenders with BOQ Breakdown', f'{len(openrows):,} open civil tenders in Odisha with estimates, closing dates and BOQ cost mix. Filter by district and department.', body,
     crumbs=[('Tenders', '/tenders/')], prio=0.9, freq='daily')

# districts
for d in DIST:
    rows_t = [t for t in T if t['district'] == d]; rows_o = [a for a in OPEN if a['district'] == d]
    m = market(rows_t)
    bys = sorted(C.Counter(t['seg'] for t in rows_t).items(), key=lambda x: -x[1])
    segtbl = ''.join(f'<tr><td><a href="/departments/{slug(s)}/">{E(s)}</a></td><td class="n">{n}</td><td class="n">{pct(market([t for t in rows_t if t["seg"]==s])["med"])}</td>'
                     f'<td class="n">{market([t for t in rows_t if t["seg"]==s])["par"]:.0%}</td></tr>' for s, n in bys if n >= 3)
    body = (f'<h1>Tenders in {E(d)} district</h1><p class="lede">{len([a for a in rows_o if not a["closed"]])} open civil tenders and how {len(rows_t):,} tenders were won in {E(d)} in 2026.</p>'
            f'<section><h2>How {E(d)} bids</h2>{mkt_block(m, d)}' +
            (f'<div class="tbl"><table><thead><tr><th>Department</th><th class="n">Tenders</th><th class="n">Median winning bid</th><th class="n">Won at par</th></tr></thead><tbody>{segtbl}</tbody></table></div>' if segtbl else '') +
            f'</section>{cta(f"See every regular bidder in {d}, what they usually quote, and your win chance at any bid.")}'
            f'<section><h2>Open tenders in {E(d)}</h2>{tender_rows(rows_o, show_dist=False)}</section>')
    jl = [{"@context": "https://schema.org", "@type": "Dataset", "name": f"Odisha tender results in {d} district, 2026",
           "description": f"Winning bids for {len(rows_t)} civil tenders in {d} district, Odisha, 2026.", "creator": {"@type": "Organization", "name": BRAND},
           "isBasedOn": "https://tendersodisha.gov.in", "temporalCoverage": "2026-01-03/2026-11-10", "spatialCoverage": f"{d}, Odisha, India"}]
    page(f'/districts/{slug(d)}/', f'{d} Tenders 2026: Open Works and Winning Bids', f'Open civil tenders in {d}, Odisha, and how they are won: median winning bid {pct(m["med"]) if m else "–"}, share won at par, departments and BOQ types.',
         body, crumbs=[('Districts', '/districts/'), (d, f'/districts/{slug(d)}/')], jsonld=jl, prio=0.8)
rows = ''.join(f'<tr><td><a href="/districts/{slug(d)}/">{E(d)}</a></td><td class="n">{len([a for a in OPEN if a["district"]==d and not a["closed"]])}</td>'
               f'<td class="n">{len([t for t in T if t["district"]==d]):,}</td><td class="n">{pct((market([t for t in T if t["district"]==d]) or {"med":None})["med"])}</td></tr>' for d in DIST)
page('/districts/', 'Odisha Tenders by District', 'All 30 Odisha districts: open civil tenders and how winning bids behave in each.',
     f'<h1>Odisha tenders by district</h1><p class="lede">Open tenders and 2026 winning-bid patterns for every district.</p><div class="tbl"><table><thead><tr><th>District</th><th class="n">Open tenders</th><th class="n">Decided in 2026</th><th class="n">Median winning bid</th></tr></thead><tbody>{rows}</tbody></table></div>',
     crumbs=[('Districts', '/districts/')], prio=0.8)

# departments
for s in SEGS:
    rows_t = [t for t in T if t['seg'] == s]; rows_o = [a for a in OPEN if a['seg'] == s]; m = market(rows_t)
    bk = []
    for lo, hi, lab in [(1, 2, '1–2'), (3, 7, '3–7'), (8, 15, '8–15'), (16, 999, '16+')]:
        mm = market([t for t in rows_t if lo <= t['npriced'] <= hi])
        if mm and mm['n'] >= 5: bk.append(f'<tr><td>{lab} bidders</td><td class="n">{mm["n"]}</td><td class="n">{pct(mm["med"])}</td><td class="n">{mm["par"]:.0%}</td></tr>')
    body = (f'<h1>{E(s)} tenders in Odisha</h1><p class="lede">{len([a for a in rows_o if not a["closed"]])} open tenders. {len(rows_t):,} tenders decided in 2026.</p>'
            f'<section><h2>How this department’s tenders are won</h2>{mkt_block(m, s)}' +
            (f'<h3>Crowd size changes the outcome</h3><div class="tbl"><table><thead><tr><th>Bidders</th><th class="n">Tenders</th><th class="n">Median winning bid</th><th class="n">Won at par</th></tr></thead><tbody>{"".join(bk)}</tbody></table></div>' if bk else '') +
            f'</section>{cta()}<section><h2>Open tenders</h2>{tender_rows(rows_o)}</section>')
    page(f'/departments/{slug(s)}/', f'{s} Tenders Odisha: Open Works and Winning Bids', f'{s}: open tenders in Odisha and how they are won in 2026 – median winning bid {pct(m["med"]) if m else "–"}, at-par share and the effect of crowd size.',
         body, crumbs=[('Departments', '/departments/'), (s, f'/departments/{slug(s)}/')], prio=0.8)
page('/departments/', 'Odisha Tenders by Department', 'Rural Works, Works Department, Water Resources, municipal bodies and more: open tenders and winning-bid patterns.',
     '<h1>Odisha tenders by department</h1><div class="tbl"><table><thead><tr><th>Department</th><th class="n">Open</th><th class="n">Decided 2026</th><th class="n">Median winning bid</th><th class="n">Won at par</th></tr></thead><tbody>' +
     ''.join(f'<tr><td><a href="/departments/{slug(s)}/">{E(s)}</a></td><td class="n">{len([a for a in OPEN if a["seg"]==s and not a["closed"]])}</td><td class="n">{len([t for t in T if t["seg"]==s]):,}</td>'
             f'<td class="n">{pct((market([t for t in T if t["seg"]==s]) or {"med":None})["med"])}</td><td class="n">{(market([t for t in T if t["seg"]==s]) or {"par":0})["par"]:.0%}</td></tr>' for s in SEGS) + '</tbody></table></div>',
     crumbs=[('Departments', '/departments/')], prio=0.8)

# work types (BOQ-based for open tenders)
for w in WTS:
    rows_o = [a for a in OPEN if a['wt'] == w]
    if not rows_o: continue
    mixes = [MIX[a['id']]['mix'] for a in rows_o]
    agg = C.Counter()
    for mx in mixes: agg.update(mx)
    tot = sum(agg.values()) or 1; avg = {k: v / tot for k, v in agg.items()}
    ests = sorted(a['est'] for a in rows_o)
    body = (f'<h1>{E(w)} tenders in Odisha</h1><p class="lede">{len(rows_o):,} open tenders whose BOQ is mainly {E(w.lower())}. Median estimate {inr(st.median(ests))}.</p>'
            f'<section><h2>Typical cost mix</h2>{mixbar(avg, 8)}<p class="muted">Average share of BOQ value across these tenders.</p></section>{cta()}'
            f'<section><h2>Open tenders</h2>{tender_rows(rows_o)}</section>')
    page(f'/work-types/{WT_SLUG[w]}/', f'{w} Tenders in Odisha with BOQ Cost Mix', f'{len(rows_o)} open {w.lower()} tenders in Odisha with their BOQ cost mix: concrete, steel, bitumen, pipes, stone and earthwork shares.',
         body, crumbs=[('Work types', '/work-types/'), (w, f'/work-types/{WT_SLUG[w]}/')], prio=0.7)
page('/work-types/', 'Odisha Tenders by Work Type (from the BOQ)', 'Odisha civil tenders grouped by what their BOQ actually contains: concrete structures, buildings, pipelines, bituminous roads, earth roads.',
     '<h1>Tenders by work type</h1><p class="lede">Grouped by where the money goes in each tender’s BOQ, not just its title.</p><ul class="cards">' +
     ''.join(f'<li><a href="/work-types/{WT_SLUG[w]}/"><b>{E(w)}</b><span>{len([a for a in OPEN if a["wt"]==w]):,} tenders</span></a></li>' for w in WTS) + '</ul>',
     crumbs=[('Work types', '/work-types/')], prio=0.7)

# guides
G = json.load(open(HERE + '/guides.json'))
for g in G:
    page(f'/guides/{g["slug"]}/', g['title'], g['desc'], f'<article class="prose"><h1>{E(g["h1"])}</h1>{g["html"]}</article>{cta()}',
         crumbs=[('Guides', '/guides/'), (g['h1'], f'/guides/{g["slug"]}/')],
         jsonld=[{"@context": "https://schema.org", "@type": "Article", "headline": g['h1'], "datePublished": "2026-11-12", "author": {"@type": "Organization", "name": BRAND}}] +
                ([{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g['faq']]}] if g.get('faq') else []),
         prio=0.7, freq='monthly')
page('/guides/', 'Guides for Odisha Tender Bidders', 'Plain guides on Odisha tender rules, at-par draws, reading a BOQ and pricing a bid.',
     '<h1>Guides</h1><ul class="cards">' + ''.join(f'<li><a href="/guides/{g["slug"]}/"><b>{E(g["h1"])}</b><span>{E(g["desc"])}</span></a></li>' for g in G) + '</ul>',
     crumbs=[('Guides', '/guides/')], prio=0.6, freq='monthly')

# pricing, signup, about, home
TIERS = json.load(open(HERE + '/tiers.json'))
ptbl = ('<div class="tbl"><table class="tiers"><thead><tr><th>Feature</th><th>Free</th><th>Pro</th><th>Business</th></tr></thead><tbody>' +
        ''.join(f'<tr><td>{E(f[0])}</td>' + ''.join(f'<td>{E(x)}</td>' for x in f[1:]) + '</tr>' for f in TIERS['features']) + '</tbody></table></div>')
plans = ''.join(f'<div class="plan{" hl" if p.get("hl") else ""}"><h2>{E(p["name"])}</h2><p class="price">{E(p["price"])}</p><p>{E(p["for"])}</p><a class="btn{" ghost" if not p.get("hl") else ""}" href="/signup/">{E(p["cta"])}</a></div>' for p in TIERS['plans'])
page('/pricing/', 'Pricing | Odisha Tender Desk', 'Free tender list, BOQ summaries and your own bid profile. Pro and Business add rival profiles, the full bid estimator and alerts.',
     f'<h1>Pricing</h1><p class="lede">Start free. Upgrade when the numbers start paying for themselves; one won tender usually covers years of Pro.</p><div class="plans">{plans}</div><h2>Compare plans</h2>{ptbl}<p class="muted">Introductory prices, subject to change. GST extra.</p>',
     crumbs=[('Pricing', '/pricing/')], prio=0.8, freq='monthly')
form_action = FORM_ENDPOINT or '#'
page('/signup/', 'Get Your Free Bid Profile | Odisha Tender Desk', 'Sign up free to see your own Odisha tender bid history, wins and draws, and get the open-tender list with BOQ breakdowns.',
     f'''<h1>Get your free bid profile</h1><p class="lede">Tell us the name you bid under. We’ll send your 2026 bid history: every tender, your %, your rank and the regulars you meet.</p>
<form class="signup" method="post" action="{E(form_action)}"><label for="n">Your name</label><input id="n" name="name" required autocomplete="name">
<label for="b">Name you bid under on the portal</label><input id="b" name="bidder_name" required>
<label for="p">Mobile number</label><input id="p" name="mobile" type="tel" required autocomplete="tel" inputmode="tel">
<label for="d">Main district</label><select id="d" name="district"><option value="">Choose</option>{"".join(f"<option>{E(x)}</option>" for x in DIST)}</select>
<label class="chk"><input type="checkbox" name="consent" value="yes" required> I agree to be contacted about my profile and {BRAND} plans by call, SMS or WhatsApp. I can opt out any time.</label>
<button class="btn" type="submit">Send my profile</button></form>
<p class="muted">We use your number only to share your profile and our plans. We never share it with other bidders.</p>''',
     crumbs=[('Sign up', '/signup/')], prio=0.7, freq='monthly')
page('/about/', 'About the Data | Odisha Tender Desk', 'Where the data comes from, what it covers and what it does not.',
     f'''<article class="prose"><h1>About the data</h1><p>All figures come from public pages of <a href="https://tendersodisha.gov.in/nicgep/app" rel="nofollow noopener">tendersodisha.gov.in</a>: tender notices, results of tenders and department BOQs published while a tender is open. Each result is checked against its own tender ID.</p>
<h2>What we cover</h2><p>Odisha state civil works tendered online since 3 January 2026, when Works Department OM No. 173/W removed the 14.99% cap on below-estimate bids: {len(T):,} decided tenders and every priced bid in them, plus {len(OPEN):,} open tenders and {len(BOQ):,} BOQs.</p>
<h2>What we don’t cover</h2><p>Central agencies in Odisha (NHAI, Railways, PSUs) that tender elsewhere, small works handled offline, and anything after award: agreements, extra items, delays and payments.</p>
<h2>Bidder privacy</h2><p>Bid histories are shown only to signed-in users, and bidder names are not published on public pages or in search engines.</p></article>''',
     crumbs=[('About', '/about/')], prio=0.4, freq='monthly')

closing = sorted([a for a in OPEN if not a['closed']], key=lambda a: pdate(a.get('close')) or DT.date(2100, 1, 1))[:12]
home_faq = [("Is the tender data official?", "It comes from public pages of tendersodisha.gov.in. Always download documents and submit bids on the official portal."),
            ("What does ‘won at par’ mean?", "The lowest bid was between 0% and −1% of the estimate. In crowded Rural Works tenders many bidders quote exactly at par and the work goes by draw."),
            ("Do you show who will bid on a tender?", "No. Nobody can know that before bids open. We show past results and each bidder’s history so you can price independently."),
            ("Is it free?", "The tender list, BOQ summaries, district and department pages and your own bid profile are free. Rival profiles, the full estimator and alerts are paid.")]
body = (f'''<section class="hero"><h1>Find the right Odisha tender, and the right bid</h1>
<p class="lede">{len([a for a in OPEN if not a["closed"]]):,} open civil tenders, updated twice a day, with what each market usually bids.</p>
<form class="search" action="/tenders/" method="get" role="search"><input name="q" type="search" placeholder="Search work, place or tender ID" aria-label="Search tenders"><button class="btn" type="submit">Search</button></form></section>
<section><h2>Closing soon</h2>{tender_rows(closing, 8, fold=99)}<p><a href="/tenders/">See all open tenders →</a></p></section>
<section><h2>Three things to know before you price</h2><ol class="know">
<li><b>{pct(market([t for t in T if t["seg"]=="Rural Works (CE RW I)"])["med"])}</b> Rural Works: most tenders are won at par and settled by draw.</li>
<li><b>{pct(market([t for t in T if t["seg"]=="Works Dept (EIC-Civil)"])["med"])}</b> Works Department: few bidders, real price fights.</li>
<li><b>{pct(market([t for t in T if 3<=t["npriced"]<=7])["med"])}</b> when 3–7 contractors bid, but {pct(market([t for t in T if t["npriced"]>=16])["med"])} with 16 or more.</li></ol>
<p class="muted">From {len(T):,} tenders decided in 2026 and {sum(t["npriced"] for t in T):,} bids.</p></section>
<section><h2>Browse by district</h2><p class="taglist">{" ".join(f'<a href="/districts/{slug(d)}/">{E(d)}</a>' for d in DIST)}</p></section>
<section class="band"><h2>See what your rivals bid</h2><p>Your own bid history is free. Rival profiles, the bid estimator and alerts are on Pro.</p><p><a class="btn" href="/signup/">Get your free profile</a> <a class="btn ghost" href="/pricing/">See pricing</a></p></section>
<section><h2>Questions</h2>{"".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q,a in home_faq)}</section>''')
page('/', f'{BRAND}: Odisha Tender Results, BOQs and Bid Analysis', 'Open Odisha civil tenders with BOQ breakdowns, 2026 winning-bid patterns by district and department, and bidder intelligence for contractors.',
     body, jsonld=[{"@context": "https://schema.org", "@type": "Organization", "name": BRAND, "url": SITE_URL},
                   {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": SITE_URL},
                   {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in home_faq]}],
     prio=1.0, freq='daily')

# app placeholder (sign-in area, never indexed)
page('/app/', 'Sign in | Odisha Tender Desk', 'Sign in to Odisha Tender Desk.', '<h1>Sign in</h1><p>The member area opens with launch. <a href="/signup/">Get your free profile</a> meanwhile.</p>', crumbs=[('Sign in', '/app/')], noindex=True)

# 404, robots, sitemap
open(OUT + '/404.html', 'w').write(open(OUT + '/about/index.html').read().replace('<h1>About the data</h1>', '<h1>Page not found</h1><p><a href="/">Go to the home page</a></p><h2>About the data</h2>', 1))
open(OUT + '/robots.txt', 'w').write(f'User-agent: *\nAllow: /\nDisallow: /app/\n\nSitemap: {SITE_URL}/sitemap.xml\n')
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
    f'<url><loc>{SITE_URL}{p}</loc><lastmod>{lm.isoformat()}</lastmod><changefreq>{f}</changefreq><priority>{pr:.1f}</priority></url>\n' for p, pr, f, lm in PAGES) + '</urlset>\n'
open(OUT + '/sitemap.xml', 'w').write(sm)
print('pages', len(PAGES), 'tenders', len(OPEN), 'districts', len(DIST), 'segs', len(SEGS))

# ---- base-path rewrite for project sites (e.g. GitHub Pages /repo/)
BASE = os.environ.get('BASE', '').rstrip('/')
if BASE:
    for root, _, files in os.walk(OUT):
        for f in files:
            p = os.path.join(root, f)
            if f.endswith('.html'):
                s = open(p).read()
                s = re.sub(r'(href|action)="/(?!/)', lambda m: f'{m.group(1)}="{BASE}/', s)
                s = s.replace('fetch("/assets/', f'fetch("{BASE}/assets/')
                open(p, 'w').write(s)
            elif f == 'tenders.json':
                s = open(p).read().replace('"/tenders/', f'"{BASE}/tenders/')
                open(p, 'w').write(s)
    print('base rewritten', BASE)
