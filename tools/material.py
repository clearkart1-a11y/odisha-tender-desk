"""Classify each tender's main material/work type from title + product category,
then build bidder 'cost signatures' (how aggressive each bidder is per work type, relative to the field)."""
import json, re, statistics as st, collections as C, sys
RULES = [  # (class, regex) checked in order
 ('Bridge / culvert', r'\bbridge|\bculvert|\bH\.?L\.?\b|\bROB\b|\bcauseway|\bC\.?D\.? work|submersible|\bslab drain'),
 ('BT road', r'\bB\.?\s?T\.?\b|bitumin|black\s?top|\bSDBC\b|\bDBM\b|\bBC\b|premix|\bcarpet|surface dressing|re-?surfac|\bMSS\b|\bOGPC\b|periodical renewal|\bP\.?R\.?\b work'),
 ('CC road', r'\bC\.?\s?C\.?\s*(road|pavement|street|lane)|cement concrete (road|pavement)|\bPQC\b|concrete road|c\.c\.road|cc rd'),
 ('Water supply / pipeline', r'water supply|pipe\s?line|\bPWS\b|\bWTP\b|\bOHT\b|\bESR\b|tube\s?well|bore\s?well|drinking water|piped water|\bRWS'),
 ('Canal / irrigation', r'canal|lining|distributar|\bminor\b|sluice|\bweir\b|embankment|check\s?dam|lift irrigation|\bL\.?I\.? point|\bMIP\b|irrigation|barrage|\bdyke|spur|river bank|saline'),
 ('Drain', r'\bdrain|drainage|\bnala|nullah|storm water|sewer'),
 ('Building', r'building|school|hostel|office|quarter|\bhall\b|toilet|kitchen|anganwadi|class\s?room|\broom|hospital|\bPHC\b|\bCHC\b|college|godown|warehouse|market complex|shed|residen|bhawan|bhaban|mandap|auditorium|compound wall|boundary wall|renovation'),
 ('Road (gravel / WBM / other)', r'\broad|\bstreet|\bpath\b|footpath|\bWBM\b|moorum|gravel|earthen|approach'),
 ('Electrical', r'electric|electrif|solar|street\s?light|lighting|\bHT\b|\bLT\b line|transformer'),
 ('Pond / earthwork', r'pond|tank|earth\s?work|excavat|desilt|renovation of (tank|pond)'),
]
CATFALL = {'Roads': 'Road (gravel / WBM / other)', 'Buildings': 'Building', 'Canal': 'Canal / irrigation', 'Water Works': 'Water supply / pipeline',
           'Bridges': 'Bridge / culvert', 'Electrical Works': 'Electrical', 'Lift Irrigation Schemes': 'Canal / irrigation', 'Highways': 'BT road'}
RX = [(c, re.compile(r, re.I)) for c, r in RULES]
def classify(title, cat):
    t = title or ''
    for c, r in RX:
        if r.search(t): return c
    return CATFALL.get(cat, 'Other / mixed')

