"""Render the SAP-1 NAND controller wiring plan (rail_plan.py) to a PNG: schematic + pin table."""
import sys, os
D = os.path.dirname(os.path.abspath(__file__)); _OUT = sys.argv[1] if len(sys.argv) > 1 else None
sys.argv = ['x', 'parts']
src = open(os.path.join(D, 'rail_plan.py')).read().replace("if __name__ == '__main__': main()", '')
src = src.replace("os.path.dirname(os.path.abspath(__file__))", repr(D))
exec(src)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, Wedge

OUT = _OUT or os.path.join(D, 'SAP1_Controller_wiring.png')

# ---- reference names as Proteus numbers them (placement order) ----
REF = {'DT': 'U1', 'DO': 'U2', 'CT': 'U3'}
gates = [r for r, (t, *_ ) in PARTS.items() if t == '74LS00']
GPIN = [dict(I1=1, I2=2, O=3), dict(I1=4, I2=5, O=6), dict(I1=10, I2=9, O=8), dict(I1=13, I2=12, O=11)]
for k, r in enumerate(gates):
    REF[r] = 'U%d:%s' % (4 + k // 4, 'ABCD'[k % 4])
PN = {'74LS161': dict(D0=3, D1=4, D2=5, D3=6, ENP=7, ENT=10, CLK=2, LOAD=9, MR=1, Q0=14, Q1=13, Q2=12, Q3=11, RCO=15),
      '74154': dict(A=23, B=22, C=21, D=20, E1=18, E2=19, **{'Y%d' % i: (i + 1 if i < 11 else i + 2) for i in range(16)})}
def pinname(ref, p):
    t = PARTS[ref][0]
    if t in PN: return '%s pin %d (%s)' % (REF[ref], PN[t][p], p)
    if t == '74LS00':
        k = gates.index(ref); return '%s pin %d' % (REF[ref], GPIN[k % 4][p])
    if t == 'LOGICSTATE': return 'switch ' + ref[2:]
    if t == 'LOGICPROBE': return 'probe ' + ref[1:]
    return {'VCC': 'VCC (power)', 'GND1': 'GND', 'GND2': 'GND'}[ref]

# ---- nets from geometry ----
par = {}
def f(a):
    while par.setdefault(a, a) != a: a = par[a]
    return a
def u(a, b): par[f(a)] = f(b)
segs = []
for k, (pts, end, label) in enumerate(WIRES):
    for p in pts: u(('w', k), ('pt', p))
    for a, b in zip(pts, pts[1:]): segs.append((k, a, b))
def on(pt, a, b):
    return (a[0] == b[0] == pt[0] and min(a[1], b[1]) <= pt[1] <= max(a[1], b[1])) or \
           (a[1] == b[1] == pt[1] and min(a[0], b[0]) <= pt[0] <= max(a[0], b[0]))
for k, (pts, end, label) in enumerate(WIRES):
    for p in (pts[0], pts[-1]):
        for k2, a, b in segs:
            if k2 != k and on(p, a, b): u(('w', k), ('w', k2))
NETNAME = {}
for k, (pts, end, label) in enumerate(WIRES):
    n = label.split()[0]
    n = {'GND1': 'GND', 'GND2': 'GND', 'Q0': 'S0', 'Q1': 'S1', 'Q2': 'S2'}.get(n, n)
    NETNAME.setdefault(f(('w', k)), n)
nets = {}
for ref, (typ, X, Y) in PARTS.items():
    for p in GEOM[typ]:
        root = f(('pt', pin(ref, p)))
        if root in NETNAME: nets.setdefault(NETNAME[root], []).append((ref, p))
wirenet = [NETNAME[f(('w', k))] for k in range(len(WIRES))]

# ---- colours ----
PAL = ['#1f5fa8', '#c0392b', '#1e8449', '#8e44ad', '#d35400', '#117a8b', '#7d6608', '#a93226', '#2e4053',
       '#b7950b', '#6c3483', '#148f77', '#ba4a00', '#2874a6', '#922b21', '#1d8348', '#5b2c6f', '#9a7d0a']
names = sorted(nets)
COL = {n: PAL[i % len(PAL)] for i, n in enumerate(names)}
COL['GND'] = '#333333'; COL['VCC'] = '#c0392b'

fig = plt.figure(figsize=(34, 20), dpi=110)
ax = fig.add_axes([0.005, 0.03, 0.70, 0.93])
tx = fig.add_axes([0.71, 0.01, 0.285, 0.97]); tx.axis('off')
ax.set_aspect('equal'); ax.axis('off')
ax.set_xlim(-10900, 9600); ax.set_ylim(-5600, 7700)

# wires
for k, (pts, end, label) in enumerate(WIRES):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=COL[wirenet[k]], lw=1.6, solid_capstyle='round', zorder=2)
# junction dots: wire endpoints that land mid-way on another wire
for k, (pts, end, label) in enumerate(WIRES):
    for p in (pts[0], pts[-1]):
        if any(k2 != k and on(p, a, b) and p not in (a, b) for k2, a, b in segs):
            ax.add_patch(Circle(p, 38, color=COL[wirenet[k]], zorder=4))

def chipbox(ref, typ, X, Y, w, h, title):
    ax.add_patch(Rectangle((X, Y - h), w, h + 100, fc='#fbf7ea', ec='#7b241c', lw=1.5, zorder=3))
    ax.text(X + w / 2, Y + 170, '%s  %s' % (REF[ref], title), ha='center', va='bottom', fontsize=10, weight='bold', zorder=5)
    for p, (dx, dr) in GEOM[typ].items():
        px, py = X + dx, Y - dr
        left = dx < 0
        ax.plot([px, X if left else X + w], [py, py], color='#7b241c', lw=1.2, zorder=3)
        ax.text(X + (60 if left else w - 60), py, p, ha='left' if left else 'right', va='center', fontsize=6.5, zorder=5)
        ax.text(px + (60 if left else -60), py + 25, str(PN[typ][p]), ha='left' if left else 'right', va='bottom',
                fontsize=5.5, color='#7b241c', zorder=5)

for ref, (typ, X, Y) in PARTS.items():
    if typ == '74154':
        chipbox(ref, typ, X, Y, 1000, 1700, '74154  ' + ('T-state decoder' if ref == 'DT' else 'opcode decoder'))
    elif typ == '74LS161':
        chipbox(ref, typ, X, Y, 800, 1100, '74LS161 step counter')
    elif typ == '74LS00':
        k = gates.index(ref); g = GPIN[k % 4]
        body = Polygon([(X - 300, Y - 230), (X + 30, Y - 230), (X + 30, Y + 230), (X - 300, Y + 230)], closed=True,
                       fc='#fbf7ea', ec='#7b241c', lw=1.3, zorder=3)
        ax.add_patch(body)
        ax.add_patch(Wedge((X + 30, Y), 230, -90, 90, fc='#fbf7ea', ec='#7b241c', lw=1.3, zorder=3))
        ax.add_patch(Rectangle((X + 31, Y - 228), 15, 456, fc='#fbf7ea', ec='none', zorder=3))
        ax.add_patch(Circle((X + 300, Y), 40, fc='white', ec='#7b241c', lw=1.2, zorder=4))
        for p in ('I1', 'I2'):
            py = pin(ref, p)[1]
            ax.plot([X - 500, X - 300], [py, py], color='#7b241c', lw=1.2, zorder=3)
            ax.text(X - 470, py + 25, str(g[p]), fontsize=5.5, color='#7b241c', va='bottom', zorder=5)
        ax.plot([X + 340, X + 500], [Y, Y], color='#7b241c', lw=1.2, zorder=3)
        ax.text(X + 470, Y + 25, str(g['O']), fontsize=5.5, color='#7b241c', ha='right', va='bottom', zorder=5)
        outnet = NETNAME.get(f(('pt', pin(ref, 'O'))), ref[1:])
        ax.text(X - 130, Y + 290, REF[ref], ha='center', fontsize=7.5, weight='bold', zorder=5)
        ax.text(X - 130, Y - 20, outnet, ha='center', va='center', fontsize=6.5, color=COL.get(outnet, 'k'), zorder=5)
    elif typ == 'LOGICSTATE':
        ax.add_patch(Rectangle((X - 400, Y - 150), 400, 300, fc='#1f3a93', ec='k', zorder=3))
        ax.plot([X, X + 200], [Y, Y], color='#7b241c', lw=1.2, zorder=3)
        ax.text(X - 200, Y, ref[2:], color='white', ha='center', va='center', fontsize=7.5, weight='bold', zorder=5)
    elif typ == 'LOGICPROBE':
        ax.add_patch(Rectangle((X + 60, Y - 110), 220, 220, fc='white', ec='#7b241c', lw=1.2, zorder=3))
        ax.plot([X, X + 60], [Y, Y], color='#7b241c', lw=1.2, zorder=3)
        ax.text(X + 330, Y, ref[1:], fontsize=7.5, va='center', weight='bold', zorder=5)
    elif typ == 'POWER':
        ax.plot([X, X], [Y, Y + 100], color='#c0392b', lw=1.5, zorder=3)
        ax.add_patch(Polygon([(X - 90, Y + 100), (X + 90, Y + 100), (X, Y + 260)], fc='none', ec='#c0392b', lw=1.5, zorder=3))
        ax.text(X + 140, Y + 200, 'VCC', fontsize=8, color='#c0392b', weight='bold', zorder=5)
    elif typ == 'GROUND':
        ax.plot([X, X], [Y, Y - 100], color='#333', lw=1.5, zorder=3)
        for i, w in enumerate((180, 120, 60)):
            ax.plot([X - w / 2, X + w / 2], [Y - 100 - 50 * i] * 2, color='#333', lw=1.5, zorder=3)
        ax.text(X + 150, Y - 180, 'GND', fontsize=8, weight='bold', zorder=5)

# rail labels at the top of each vertical rail
for n, rx in RAILX.items():
    ys = [p[1] for k, (pts, e, l) in enumerate(WIRES) if wirenet[k] == n for p in pts if p[0] == rx]
    if ys:
        ax.text(rx, max(ys) + 60, n, rotation=90, ha='center', va='bottom', fontsize=7, color=COL[n], weight='bold', zorder=5)

ax.set_title('SAP-1 hard-wired controller — 2× 74154 + 7× 74LS00 (NAND only)    ·    every line is a real wire, all horizontal/vertical; dots = joins, plain crossings do NOT connect',
             fontsize=13, loc='left', pad=8)

# ---- connection table ----
order = ['CLK', 'S0', 'S1', 'S2', 'nCLR', 'VCC', 'GND', 'OP0', 'OP1', 'OP2', 'OP3',
         'nT1', 'nT2', 'nLI', 'nT4', 'nT5', 'nT6', 'nLDA', 'nADD', 'nSUB', 'nOUT']
rest = [n for n in names if n not in order]
lines = []
for n in order + rest:
    if n not in nets: continue
    pins_ = list(dict.fromkeys(pinname(r, p) for r, p in nets[n]))
    lines.append((n, pins_))
y = 1.0
tx.text(0, y, 'Connections (net → every pin on it)', fontsize=12, weight='bold', va='top'); y -= 0.022
for n, pins_ in lines:
    txt = ', '.join(pins_)
    # wrap
    words, cur, rows = txt.split(', '), '', []
    for w in words:
        if len(cur) + len(w) > 78: rows.append(cur.rstrip(', ')); cur = ''
        cur += w + ', '
    rows.append(cur.rstrip(', '))
    tx.text(0, y, n, fontsize=8.6, weight='bold', color=COL.get(n, 'k'), va='top', family='monospace')
    for r in rows:
        tx.text(0.13, y, r, fontsize=8.0, va='top', family='monospace'); y -= 0.0138
    y -= 0.002
y -= 0.01
notes = ['Parts: U1, U2 = 74154 (search "74154", there is no 74LS154). U3 = 74LS161.',
         'U4–U10 = 74LS00 (28 NAND gates). Gate C/D: pin 10/13 on top, 9/12 below.',
         'Switches = LOGICSTATE. Probes = LOGICPROBE. Chip VCC/GND pins are hidden.',
         'Opcodes: LDA 0000 → Y0, ADD 0001 → Y1, SUB 0010 → Y2, OUT 1110 → Y14.',
         'nLI comes straight off U1 Y2 (no gate). HLT = U2 Y15 (unused here).',
         'Test: set OP3..OP0, click CLK twice per T-state; S2S1S0 = 000 is T1.',
         'Expected: T1 EP,nLM · T2 CP · T3 nCE,nLI · LDA T4 nLM,nEI T5 nCE,nLA',
         '  ADD T4 nLM,nEI T5 nCE,nLB T6 nLA,EU · SUB = ADD + SU at T6 · OUT T4 EA,nLO',
         '  (n-signals are active-low: probe shows 0 when active)']
for t in notes:
    tx.text(0, y, t, fontsize=8.4, va='top'); y -= 0.0145
fig.savefig(OUT, dpi=110, facecolor='white')
print('saved', OUT, 'nets', len(nets))
