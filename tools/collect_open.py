"""Collect open tenders from tendersodisha.gov.in (public pages, no captcha) and merge into data/active.json.gz.

Flow: 'Tenders by Organisation' -> each organisation's list -> detail page for tenders not seen before.
Known tenders get their dates refreshed from the list (corrigenda). Closed tenders are kept for history.
Safe by design: if the portal returns nothing usable, the data file is left untouched and the script exits non-zero.
"""
import gzip, json, os, re, sys, time
import requests
from bs4 import BeautifulSoup

BASE = 'https://tendersodisha.gov.in'
ORGS = BASE + '/nicgep/app?page=FrontEndTendersByOrganisation&service=page'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'active.json.gz')
PAUSE = float(os.environ.get('PAUSE', '0.4'))     # be polite to a government server
MAX_NEW = int(os.environ.get('MAX_NEW', '5000'))

FIELDS = {'Tender ID': 'id', 'Tender Reference Number': 'ref', 'Organisation Chain': 'org', 'Title': 'title',
          'Work Description': 'wd', 'Tender Value in ₹': 'val', 'Product Category': 'pc', 'Sub category': 'sub',
          'Form Of Contract': 'form', 'Published Date': 'pub', 'Bid Submission End Date': 'close',
          'Bid Opening Date': 'open', 'Location': 'loc', 'Pincode': 'pin', 'Tenderer Class': 'cls',
          'Period Of Work(Days)': 'period', 'EMD Amount in ₹': 'emd'}

S = requests.Session()
S.headers['User-Agent'] = 'Mozilla/5.0 (compatible; OdishaTenderDesk/1.0; public tender listing)'

def get(url, tries=3):
    for k in range(tries):
        try:
            r = S.get(url if url.startswith('http') else BASE + url, timeout=60)
            if r.ok and 'Session Timed Out' not in r.text and 'session has expired' not in r.text.lower():
                time.sleep(PAUSE)
                return BeautifulSoup(r.text, 'html.parser')
        except requests.RequestException as e:
            print('  retry', k + 1, e, file=sys.stderr)
        time.sleep(5 * (k + 1))
    return None

def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()

def org_links(doc):
    out = []
    for a in doc.find_all('a', href=True):
        if 'DirectLink' in a['href'] and 'FrontEndTendersByOrganisation' in a['href']:
            tr = a.find_parent('tr'); tds = tr.find_all('td') if tr else []
            if len(tds) >= 3:
                out.append((clean(tds[1].get_text()), a['href']))
    return out

def list_rows(doc):
    rows = []
    tbl = doc.find('table', id='table')
    for tr in (tbl.find_all('tr', id=re.compile('^informal')) if tbl else []):
        td = tr.find_all('td', recursive=False)
        a = tr.find('a', href=re.compile('FrontEndViewTender'))
        if len(td) < 6 or not a: continue
        ids = re.findall(r'\[([^\[\]]*)\]', clean(td[4].get_text()))
        rows.append(dict(id=ids[-1] if ids else '', pub=clean(td[1].get_text()), close=clean(td[2].get_text()),
                         open=clean(td[3].get_text()), org=clean(td[5].get_text()), href=a['href']))
    return rows

def detail(doc):
    t = {}
    for c in doc.find_all('td', class_='td_caption'):
        k = clean(c.get_text())
        if k in FIELDS and FIELDS[k] not in t:
            v = c.find_next_sibling('td')
            t[FIELDS[k]] = clean(v.get_text()) if v else ''
    docs = []
    tbl = doc.find('table', id='workItemDocumenttable')
    for tr in (tbl.find_all('tr', id=re.compile('^informal')) if tbl else []):
        td = [clean(x.get_text()) for x in tr.find_all('td', recursive=False)]
        if len(td) >= 5: docs.append(td[:5])
    t['docs'] = docs
    return t

def main():
    old = []
    if os.path.exists(DATA):
        with gzip.open(DATA, 'rt', encoding='utf-8') as f: old = json.load(f)
    by_id = {a['id']: a for a in old}
    home = get(ORGS)
    orgs = org_links(home) if home else []
    print('organisations:', len(orgs))
    if not orgs:
        sys.exit('No organisations found: portal unreachable or layout changed. Data left untouched.')
    seen, new, upd = set(), 0, 0
    for name, href in orgs:
        doc = get(href)
        if not doc: print('  skip org', name, file=sys.stderr); continue
        rows = list_rows(doc)
        print(f'  {name}: {len(rows)}')
        for r in rows:
            if not r['id']: continue
            seen.add(r['id'])
            if r['id'] in by_id:
                a = by_id[r['id']]
                for k in ('close', 'open'):
                    if r[k] and a.get(k) != r[k]: a[k] = r[k]; upd += 1
                continue
            if new >= MAX_NEW: continue
            d = get(r['href'])
            if not d: continue
            t = detail(d)
            if t.get('id') != r['id']:   # the portal tracks one tender per session; never store a mismatch
                print('  mismatch', r['id'], t.get('id'), file=sys.stderr); continue
            t['_org'] = name
            by_id[t['id']] = t; new += 1
    if not seen:
        sys.exit('No tenders parsed. Data left untouched.')
    out = sorted(by_id.values(), key=lambda a: a['id'])
    tmp = DATA + '.tmp'
    with gzip.open(tmp, 'wt', encoding='utf-8') as f: json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, DATA)
    print(f'open now: {len(seen)}  new: {new}  date changes: {upd}  total stored: {len(out)}')

if __name__ == '__main__':
    main()
