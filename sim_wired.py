"""Live test of the wired controller: set opcode switches, clock T1..T6, read probes by fill colour."""
import subprocess, os, sys
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, '..', 'chk.py')).read().split('codes=')[0])  # ref(t, op)
_ARGS = sys.argv[1:]; sys.argv = ['x', 'parts']
src = open(os.path.join(D, 'rail_plan.py')).read().replace("if __name__ == '__main__': main()", '')
exec(src.replace("os.path.dirname(os.path.abspath(__file__))", repr(D)))

SW = {'CLK': (303, 200), 'OP0': (303, 782), 'OP1': (303, 825), 'OP2': (303, 867), 'OP3': (303, 910)}
state = {'CLK': 0, 'OP0': 1, 'OP1': 1, 'OP2': 1, 'OP3': 1}
SIG = {'Ep': ('EP', 0), 'Cp': ('CP', 0), 'Lm': ('nLM', 1), 'Ce': ('nCE', 1), 'Li': ('nLI', 1), 'Ei': ('nEI', 1),
       'La': ('nLA', 1), 'Ea': ('EA', 0), 'Su': ('SU', 0), 'Eu': ('EU', 0), 'Lb': ('nLB', 1), 'Lo': ('nLO', 1)}

def ui(*a): subprocess.run([os.path.join(D, 'pfront.sh')] + [str(x) for x in a], check=True)
def toggle(n): ui('c', *SW[n], 'w', 600); state[n] ^= 1

def read():
    subprocess.run([os.path.join(D, 'winshot.sh'), os.path.join(D, 'raw.png')], capture_output=True)
    im = Image.open(os.path.join(D, 'raw.png')).convert('RGB')
    v = {}
    for n, (X, Y) in PROBES.items():
        cx, cy = scr(X, Y)
        red = blue = 0
        for x in range(int((cx + 4) * 2), int((cx + 16) * 2)):
            for y in range(int((cy - 6) * 2), int((cy + 6) * 2)):
                r, g, b = im.getpixel((x, y))
                if r > 140 and g < 60 and b < 60: red += 1
                if b > 140 and r < 60 and g < 60: blue += 1
        if red == blue == 0: raise SystemExit('cannot read probe ' + n)
        v[n] = int(red > blue)
    return v

v = read(); print('start', v)
if _ARGS == ['read']: sys.exit()
bad = 0
for op, code in [('LDA', 0), ('ADD', 1), ('SUB', 2), ('OUT', 14), ('HLT', 15)]:
    for i in range(4):
        if state['OP%d' % i] != (code >> i & 1): toggle('OP%d' % i)
    for _ in range(6):
        v = read()
        t = v['S0'] + 2 * v['S1'] + 4 * v['S2'] + 1
        got = {k for k, (n, inv) in SIG.items() if v[n] ^ inv}
        exp = ref(t, op) if t <= 6 else {'?'}
        ok = got == exp
        bad += not ok
        print(('OK ' if ok else 'BAD'), op, 'T%d' % t, sorted(got), '' if ok else 'expected %s' % sorted(exp), flush=True)
        toggle('CLK'); toggle('CLK')
print('FAILURES:', bad, 'of 30')
