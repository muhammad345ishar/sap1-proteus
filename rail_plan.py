#!/usr/bin/env python3
"""SAP-1 hard-wired controller (NAND only) with real wires in a rail layout, A2 sheet.
Every wire is a list of orthogonal points; the first point is a pin or an existing wire,
the last is a pin / an existing wire ('end') or open space ('open', double-click).
usage: rail_plan.py place [a b] | wires [a b] | listwires | parts | check"""
import sys, json, os
D = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(D, 'map.json')))
def scr(x, y): return (round(M['cx'] + x * M.get('Sx', M['S']), 2), round(M['cy'] - y * M.get('Sy', M['S']), 2))

LIST = {'74LS00': 217.5, '74LS161': 230.5, '74154': 243.5, 'LOGICPROBE': 269.5, 'LOGICSTATE': 282.5}

def chip(left, right, rx):
    g = {}
    for n, r in left: g[n] = (-200, r)
    for n, r in right: g[n] = (rx, r)
    return g
GEOM = {
 '74LS161': chip([('D0',100),('D1',200),('D2',300),('D3',400),('ENP',600),('ENT',700),('CLK',800),
                  ('LOAD',900),('MR',1000)], [('Q0',100),('Q1',200),('Q2',300),('Q3',400),('RCO',500)], 800),
 '74154': chip([('A',100),('B',200),('C',300),('D',400),('E1',600),('E2',700)],
               [('Y%d'%i, 100*(i+1)) for i in range(16)], 1000),
 '74LS00': {'I1': (-500, -100), 'I2': (-500, 100), 'O': (500, 0)},
 'LOGICPROBE': {'P': (0, 0)}, 'LOGICSTATE': {'O': (200, 0)},
 'POWER': {'P': (0, 100)}, 'GROUND': {'P': (0, -100)},
}
PARTS = {}
def part(ref, typ, x, y): PARTS[ref] = (typ, x, y)
def pin(ref, p):
    typ, X, Y = PARTS[ref]; dx, dr = GEOM[typ][p]; return (X + dx, Y - dr)

# ---- left block ----
part('DT', '74154', -8800, 2000)
part('DO', '74154', -8800, -400)
part('CT', '74LS161', -8800, 6800)
# ---- gate matrix: one row per gate, columns by logic level ----
COLX = [-4800, -1800, 800, 2800, 4800, 6800]
# rows shared by gates whose wires never cross each other's columns (checked by 'check')
ROWSPEC = [['EP'], ['CP'], ['T4','nEU','LA','nLA'], ['T5','nADDSUB','EU'], ['T6','T5LDA','SU'],
           ['ADDSUB','nSU6','EA'], ['ILDA','nLO'], ['ISUB','nLB'], ['IOUT','T5MEM','nLM'],
           ['MEMREF','nCE'], ['nEI'], ['LM'], ['CE']]
COL = {'EP':0,'CP':0,'T4':0,'T5':0,'T6':0,'ADDSUB':0,'ILDA':0,'ISUB':0,'IOUT':0,
       'nLB':1,'nEU':1,'nADDSUB':1,'T5LDA':1,'nSU6':1,'nLO':1,
       'EU':2,'LA':2,'MEMREF':2,'SU':2,'EA':2, 'nLA':3,'nEI':3,'T5MEM':3, 'LM':4,'CE':4, 'nLM':5,'nCE':5}
def rowY(r): return 5300 - 800 * r
ROWOF = {g: r for r, gs in enumerate(ROWSPEC) for g in gs}
ORDER = [g for g in COL]               # placement order -> U4:A ...
for n in ORDER: part('g' + n, '74LS00', COLX[COL[n]], rowY(ROWOF[n]))
part('gnCLR', '74LS00', -6600, 6000)
part('swCLK', 'LOGICSTATE', -10100, 6000)
for i in range(4): part('swOP%d' % i, 'LOGICSTATE', -10100, -2200 - 600 * i)
PX = 8800
PROBES = {'S0': (-7300, 7200), 'S1': (-6600, 7000), 'S2': (-5900, 6800)}
for n in ['EP','CP','nLB','EU','SU','EA','nLA','nEI','nLM','nCE','nLO']:
    PROBES[n] = (PX, rowY(ROWOF[n]))
PROBES['nLI'] = (PX, rowY(13))
for n, (x, y) in PROBES.items(): part('p' + n, 'LOGICPROBE', x, y)
TERMS = {'VCC': ('POWER', -9800, 6400), 'GND1': ('GROUND', -9700, 900), 'GND2': ('GROUND', -9700, -1700)}
for r, (t, x, y) in TERMS.items(): part(r, t, x, y)

# ---- nets: source pin + sink pins ----
NETS = {}   # name -> (src, [sinks])
def net(n, src, *sinks): NETS[n] = (src, list(sinks))
G = lambda n, p: ('g' + n, p)
dec = {'nT1': ('DT','Y0'), 'nT2': ('DT','Y1'), 'nLI': ('DT','Y2'), 'nT4': ('DT','Y3'), 'nT5': ('DT','Y4'),
       'nT6': ('DT','Y5'), 'nLDA': ('DO','Y0'), 'nADD': ('DO','Y1'), 'nSUB': ('DO','Y2'), 'nOUT': ('DO','Y14')}
FUNC = {  # gate: (in1 net, in2 net)
 'EP': ('nT1','nT1'), 'CP': ('nT2','nT2'), 'T4': ('nT4','nT4'), 'T5': ('nT5','nT5'), 'T6': ('nT6','nT6'),
 'ADDSUB': ('nADD','nSUB'), 'ILDA': ('nLDA','nLDA'), 'ISUB': ('nSUB','nSUB'), 'IOUT': ('nOUT','nOUT'),
 'nLB': ('T5','ADDSUB'), 'nEU': ('T6','ADDSUB'), 'nADDSUB': ('ADDSUB','ADDSUB'), 'T5LDA': ('T5','ILDA'),
 'nSU6': ('T6','ISUB'), 'nLO': ('T4','IOUT'),
 'EU': ('nEU','nEU'), 'LA': ('T5LDA','nEU'), 'MEMREF': ('nLDA','nADDSUB'), 'SU': ('nSU6','nSU6'), 'EA': ('nLO','nLO'),
 'nLA': ('LA','LA'), 'nEI': ('T4','MEMREF'), 'T5MEM': ('T5','MEMREF'),
 'LM': ('nT1','nEI'), 'CE': ('nLI','T5MEM'), 'nLM': ('LM','LM'), 'nCE': ('CE','CE'),
}
sinks = {}
for g, (a, b) in FUNC.items():
    sinks.setdefault(a, []).append(G(g, 'I1')); sinks.setdefault(b, []).append(G(g, 'I2'))
# rails (x positions) per channel
RAILX = {}
for k, n in enumerate(['nT1','nT2','nLI','nT4','nT5','nT6','nLDA','nADD','nSUB','nOUT']): RAILX[n] = -7400 + 200 * k
for k, n in enumerate(['T4','T5','T6','ADDSUB','ILDA','ISUB','IOUT']): RAILX[n] = -3900 + 200 * k
for k, n in enumerate(['nADDSUB','T5LDA','nEU','nSU6','nLO']): RAILX[n] = -900 + 200 * k
RAILX['MEMREF'], RAILX['LA'] = 1700, 1900
RAILX['nEI'], RAILX['T5MEM'] = 3700, 3900
RAILX['LM'], RAILX['CE'] = 5700, 5900

WIRES = []  # (points, endkind, label)
def wire(pts, end, label): WIRES.append((pts, end, label))

def rail_net(n, src_pin, extra_points=()):
    """source -> rail; rail spans all sink rows; taps from each sink pin."""
    sx, sy = src_pin; rx = RAILX[n]
    ys = [pin(*s)[1] for s in sinks.get(n, [])] + [y for _, y in extra_points] + [sy]
    lo, hi = min(ys), max(ys)
    if lo < sy:
        wire([src_pin, (rx, sy), (rx, lo)], 'open', n + ' rail down')
        if hi > sy: wire([(rx, sy), (rx, hi)], 'open', n + ' rail up')
    else:
        wire([src_pin, (rx, sy), (rx, hi)], 'open', n + ' rail up')
    for s in sinks.get(n, []):
        p = pin(*s); wire([p, (rx, p[1])], 'end', '%s -> %s.%s' % (n, s[0], s[1]))

# --- counter / clock / power ---
Q = {k: pin('CT', 'Q%d' % k) for k in range(3)}
qx1 = {0: -7700, 1: -7800, 2: -7900}; qy = {0: 5300, 1: 5500, 2: 5400}; qx2 = {0: -9300, 1: -9200, 2: -9100}
for k, tp in enumerate('ABC'):
    a = Q[k]; b = pin('DT', tp)
    wire([a, (qx1[k], a[1]), (qx1[k], qy[k]), (qx2[k], qy[k]), (qx2[k], b[1]), b], 'end', 'Q%d -> DT.%s' % (k, tp))
for k in range(3):
    pp = pin('pS%d' % k, 'P'); wire([pp, (qx1[k], pp[1]), (qx1[k], Q[k][1])], 'end', 'Q%d probe' % k)
wire([pin('gnCLR', 'I1'), (qx1[1], pin('gnCLR', 'I1')[1])], 'end', 'Q1 nCLR')
wire([pin('gnCLR', 'I2'), (qx1[2], pin('gnCLR', 'I2')[1])], 'end', 'Q2 nCLR')
o = pin('gnCLR', 'O'); mr = pin('CT', 'MR')
wire([o, (-6000, o[1]), (-6000, 7400), (-9600, 7400), (-9600, mr[1]), mr], 'end', 'nCLR MR')
wire([pin('swCLK', 'O'), pin('CT', 'CLK')], 'end', 'CLK')
v = pin('VCC', 'P'); ld = pin('CT', 'LOAD')
wire([v, (v[0], ld[1]), ld], 'end', 'VCC LOAD')
for p in ('ENP', 'ENT'): q = pin('CT', p); wire([q, (v[0], q[1])], 'end', 'VCC ' + p)
g1 = pin('GND1', 'P'); d = pin('DT', 'D')
wire([g1, (g1[0], d[1]), d], 'end', 'GND1 D')
for p in ('E1', 'E2'): q = pin('DT', p); wire([q, (g1[0], q[1])], 'end', 'GND1 ' + p)
g2 = pin('GND2', 'P'); e1 = pin('DO', 'E1')
wire([g2, (g2[0], e1[1]), e1], 'end', 'GND2 E1')
q = pin('DO', 'E2'); wire([q, (g2[0], q[1])], 'end', 'GND2 E2')
opx = {0: -9300, 1: -9400, 2: -9500, 3: -9600}
for k, tp in enumerate('ABCD'):
    a = pin('swOP%d' % k, 'O'); b = pin('DO', tp)
    wire([a, (opx[k], a[1]), (opx[k], b[1]), b], 'end', 'OP%d %s' % (k, tp))
# --- rails ---
for n, (r, p) in dec.items():
    extra = [(0, rowY(13))] if n == 'nLI' else []
    rail_net(n, pin(r, p), extra)
for n in ['T4','T5','T6','ADDSUB','ILDA','ISUB','IOUT','nADDSUB','T5LDA','nEU','nSU6','nLO','MEMREF','LA','nEI','T5MEM','LM','CE']:
    rail_net(n, pin('g' + n, 'O'))
# --- probes (drawn from the probe pin leftwards) ---
for n in ['EP','CP','nLB','EU','SU','EA','nLA','nLM','nCE']:
    wire([pin('p' + n, 'P'), pin('g' + n, 'O')], 'end', n + ' probe')
for n in ['nEI', 'nLO']:
    p = pin('p' + n, 'P'); wire([p, (RAILX[n], p[1])], 'end', n + ' probe')
p = pin('pnLI', 'P'); wire([p, (RAILX['nLI'], p[1])], 'end', 'nLI probe')

EMPTY = scr(9800, -7200)  # safe only in Selection mode
def T(*a): return [str(v) for v in a]
def main():
    mode = sys.argv[1]; lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
    out = []
    if mode == 'place':
        for k, (ref, (typ, X, Y)) in enumerate(PARTS.items()):
            if not (lo <= k < hi) or typ in ('POWER', 'GROUND'): continue
            x, y = scr(X, Y)
            out += T('c', 60, LIST[typ], 'w', 250, 'm', x, y, 'w', 250, 'c', x, y, 'w', 400, 'm', x, y, 'w', 150, 'c', x, y, 'w', 500)
    elif mode == 'wires':
        for k, (pts, end, label) in enumerate(WIRES):
            if not (lo <= k < hi): continue
            out += T('c', *EMPTY, 'w', 150)
            for i, pt in enumerate(pts):
                x, y = scr(*pt)
                last = i == len(pts) - 1
                out += T('m', x - 3, y + 2, 'w', 120, 'm', x, y, 'w', 250)
                out += T('dc' if (last and end == 'open') else 'c', x, y, 'w', 300 if not last else 450)
            out += T('k', 'esc', 'w', 120)
    elif mode == 'listwires':
        for k, (pts, end, label) in enumerate(WIRES): print(k, label, end, pts)
        return
    elif mode == 'parts':
        for k, (ref, v) in enumerate(PARTS.items()): print(k, ref, *v)
        return
    elif mode == 'check':
        check(); return
    print(' '.join(out))

def check():
    """Geometric sanity: every segment orthogonal; report collinear overlaps between different nets."""
    segs = []
    for k, (pts, end, label) in enumerate(WIRES):
        for a, b in zip(pts, pts[1:]):
            assert a[0] == b[0] or a[1] == b[1], ('diagonal', label, a, b)
            segs.append((k, label, a, b))
    bad = 0
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            k1, l1, a1, b1 = segs[i]; k2, l2, a2, b2 = segs[j]
            n1 = l1.split()[0]; n2 = l2.split()[0]
            if a1[0] == b1[0] == a2[0] == b2[0]:   # both vertical same x
                lo1, hi1 = sorted([a1[1], b1[1]]); lo2, hi2 = sorted([a2[1], b2[1]])
                if min(hi1, hi2) > max(lo1, lo2) and n1 != n2: bad += 1; print('V-OVERLAP', l1, '|', l2)
            if a1[1] == b1[1] == a2[1] == b2[1]:
                lo1, hi1 = sorted([a1[0], b1[0]]); lo2, hi2 = sorted([a2[0], b2[0]])
                if min(hi1, hi2) > max(lo1, lo2) and n1 != n2: bad += 1; print('H-OVERLAP', l1, '|', l2)
    def on(pt, a, b):
        return (a[0] == b[0] == pt[0] and min(a[1], b[1]) <= pt[1] <= max(a[1], b[1])) or \
               (a[1] == b[1] == pt[1] and min(a[0], b[0]) <= pt[0] <= max(a[0], b[0]))
    pins = {}
    for ref, (typ, X, Y) in PARTS.items():
        for p in GEOM[typ]: pins[pin(ref, p)] = ref + '.' + p
    for k, (pts, end, label) in enumerate(WIRES):
        n = label.split()[0]
        for i, pt in enumerate(pts):
            for (k2, l2, a, b) in segs:
                if k2 != k and l2.split()[0] != n and on(pt, a, b):
                    bad += 1; print('POINT-ON-OTHER-NET', label, pt, '|', l2)
            if 0 < i < len(pts) - 1 and pt in pins: bad += 1; print('CORNER-ON-PIN', label, pt, pins[pt])
        # segments passing over a foreign pin end
        for a, b in zip(pts, pts[1:]):
            for pp, nm in pins.items():
                if on(pp, a, b) and pp not in (pts[0], pts[-1]): bad += 1; print('CROSSES-PIN', label, nm)
    print(len(WIRES), 'wires,', len(segs), 'segments,', bad, 'problems')

if __name__ == '__main__': main()
