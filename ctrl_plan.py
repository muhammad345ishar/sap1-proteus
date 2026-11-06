#!/usr/bin/env python3
"""SAP-1 hard-wired controller (2x 74154 + 7x 74LS00) build plan for Proteus, A3 sheet, F8 view.
usage: ctrl_plan.py place|stubs|labels [first] [last] | list | compare File.SDF"""
import sys, json, os
M = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'map.json')))
S = M['S']
def scr(x, y): return (round(M['cx'] + x * S, 2), round(M['cy'] - y * S, 2))

LIST = {'74LS00': 217.5, '74LS161': 230.5, '74154': 243.5, 'LOGICPROBE': 269.5, 'LOGICSTATE': 282.5}

def chip(left, right, rx):
    g = {}
    for n, r in left: g[n] = (-200, r, 'L')
    for n, r in right: g[n] = (rx, r, 'R')
    return g
GEOM = {
 '74LS161': chip([('D0',100),('D1',200),('D2',300),('D3',400),('ENP',600),('ENT',700),('CLK',800),
                  ('LOAD',900),('MR',1000)], [('Q0',100),('Q1',200),('Q2',300),('Q3',400),('RCO',500)], 800),
 '74154': chip([('A',100),('B',200),('C',300),('D',400),('E1',600),('E2',700)],
               [('Y%d'%i, 100*(i+1)) for i in range(16)], 1000),
 '74LS00': {'I1': (-500, -100, 'L'), 'I2': (-500, 100, 'L'), 'O': (500, 0, 'R')},
 'LOGICPROBE': {'P': (0, 0, 'L')},
 'LOGICSTATE': {'O': (200, 0, 'R')},
}

PARTS = []  # (ref, type, X, Y, {pin: net})
PARTS.append(('DT', '74154', -4800, 2900, dict(A='S0', B='S1', C='S2', D='GND', E1='GND', E2='GND',
              Y0='nT1', Y1='nT2', Y2='nLI', Y3='nT4', Y4='nT5', Y5='nT6')))
PARTS.append(('DO', '74154', -4800, 900, dict(A='OP0', B='OP1', C='OP2', D='OP3', E1='GND', E2='GND',
              Y0='nLDA', Y1='nADD', Y2='nSUB', Y14='nOUT')))
PARTS.append(('CT', '74LS161', -4800, 4500, dict(CLK='CLK', MR='nCLR', ENP='VCC', ENT='VCC', LOAD='VCC',
              D0='GND', D1='GND', D2='GND', D3='GND', Q0='S0', Q1='S1', Q2='S2')))
GATES = [  # (in1, in2, out)  -> 28 NANDs, packed 4 per 74LS00 in this order
 ('nT1','nT1','EP'), ('nT2','nT2','CP'), ('nT4','nT4','T4'), ('nT5','nT5','T5'),
 ('nT6','nT6','T6'), ('nLDA','nLDA','ILDA'), ('nSUB','nSUB','ISUB'), ('nOUT','nOUT','IOUT'),
 ('nADD','nSUB','ADDSUB'), ('ADDSUB','ADDSUB','nADDSUB'), ('nLDA','nADDSUB','MEMREF'), ('T4','MEMREF','nEI'),
 ('nT1','nEI','LM'), ('LM','LM','nLM'), ('T5','MEMREF','T5MEM'), ('nLI','T5MEM','CE'),
 ('CE','CE','nCE'), ('T5','ILDA','T5LDA'), ('T6','ADDSUB','nEU'), ('T5LDA','nEU','LA'),
 ('LA','LA','nLA'), ('nEU','nEU','EU'), ('T5','ADDSUB','nLB'), ('T4','IOUT','nLO'),
 ('nLO','nLO','EA'), ('T6','ISUB','nSU6'), ('nSU6','nSU6','SU'), ('S1','S2','nCLR'),
]
COLS = [-1700, 1000, 3700, 6400]
ROWS = [4200, 3000, 1800, 600, -600, -1800, -3000]
for k, (a, b, o) in enumerate(GATES):
    PARTS.append(('G%d' % k, '74LS00', COLS[k // 7], ROWS[k % 7], dict(I1=a, I2=b, O=o)))
for k, net in enumerate(['CLK', 'OP0', 'OP1', 'OP2', 'OP3']):
    PARTS.append(('L%d' % k, 'LOGICSTATE', -6900, [4300, 800, 300, -200, -700][k], dict(O=net)))
PROBES = ['S0','S1','S2','CP','EP','nLM','nCE','nLI','nEI','nLA','EA','SU','EU','nLB','nLO']
for k, net in enumerate(PROBES):
    PARTS.append(('P%d' % k, 'LOGICPROBE', -6300 + k * 950, -4300, dict(P=net)))

STUB_L, STUB_R = 500, 300

def pins():
    for ref, typ, X, Y, nets in PARTS:
        for pin, net in nets.items():
            dx, dr, side = GEOM[typ][pin]
            px, py = X + dx, Y - dr
            ex = px - STUB_L if side == 'L' else px + STUB_R
            yield ref, typ, pin, net, (px, py), (ex, py), side

def T(*a): return [str(v) for v in a]

def main():
    mode = sys.argv[1]; lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
    out = []
    if mode == 'place':
        for k, (ref, typ, X, Y, _) in enumerate(PARTS):
            if not (lo <= k < hi): continue
            x, y = scr(X, Y)
            out += T('c', 60, LIST[typ], 'w', 250, 'm', x, y, 'w', 250, 'c', x, y, 'w', 400, 'm', x, y, 'w', 150, 'c', x, y, 'w', 500)
    elif mode == 'stubs':
        for k, (ref, typ, pin, net, p, e, side) in enumerate(pins()):
            if not (lo <= k < hi): continue
            a = scr(*p); b = scr(*e)
            out += T('m', a[0], a[1], 'w', 120, 'c', a[0], a[1], 'w', 150, 'm', b[0], b[1], 'w', 120, 'dc', b[0], b[1], 'w', 250)
    elif mode == 'list':
        for k, row in enumerate(pins()): print(k, *row)
        return
    elif mode == 'parts':
        for k, p in enumerate(PARTS): print(k, *p[:4])
        return
    print(' '.join(out))

# Physical pin numbers for the netlist check
PN = {
 '74LS161': dict(D0=3,D1=4,D2=5,D3=6,ENP=7,ENT=10,CLK=2,LOAD=9,MR=1,Q0=14,Q1=13,Q2=12,Q3=11,RCO=15),
 '74154': dict(A=23,B=22,C=21,D=20,E1=18,E2=19,**{'Y%d'%i: (i+1 if i < 11 else i+2) for i in range(16)}),
}
GPINS = [(1,2,3),(4,5,6),(10,9,8),(13,12,11)]

def compare_netlist(sdf_path, refmap):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sdf_nets import parse_sdf
    got, _ = parse_sdf(sdf_path)
    norm = lambda s: (s or '').upper().replace('VCC/VDD', 'VCC')
    bad = n = 0
    for ref, typ, pin, net, *_ in pins():
        if typ in PN: key = (refmap[ref], PN[typ][pin])
        elif typ == '74LS00':
            k = int(ref[1:]); a, b, o = GPINS[k % 4]
            key = ('U%d' % (refmap['G0'] + k // 4), {'I1': a, 'I2': b, 'O': o}[pin])
        else: continue
        n += 1
        if norm(got.get(key)) != norm(net):
            bad += 1; print('MISMATCH', ref, pin, key, 'expected', net, 'got', got.get(key))
    print(n, 'chip pins checked,', bad, 'mismatches')

if __name__ == '__main__':
    if sys.argv[1] == 'compare':
        compare_netlist(sys.argv[2], {'DT': 'U1', 'DO': 'U2', 'CT': 'U3', 'G0': 4})
    else: main()
