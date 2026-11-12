"""Map a department name to one of 8 market segments."""
def seg(d):
    d = d or ''
    if d == 'CE RW I': return 'Rural Works (CE RW I)'
    if d == 'Municipal Bodies' or 'Municipal' in d: return 'Municipal bodies (ULBs)'
    if d == 'EIC-CIVIL': return 'Works Dept (EIC-Civil)'
    if d.startswith('Panchayati'): return 'Panchayati Raj & Drinking Water'
    if d.startswith('ST and SC'): return 'ST & SC Development'
    if d.startswith(('WATCO', 'PHEO', 'Rural Water')): return 'Water supply (WATCO / PHEO / RWSS)'
    if (d.startswith(('CE-BM', 'CE AND BM', 'CE and BM', 'CE BM', 'CCE', 'CE,Minor', 'CE,Drainage', 'Chief Engineer Mech'))
            or 'Irrigation' in d or 'Irr.' in d):
        return 'Water Resources (basins & irrigation)'
    return 'Other agencies'
