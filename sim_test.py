"""Drive the running Proteus sim: set opcode switches, clock T1..T6, read the 15 probes by colour."""
import subprocess, time, os, sys
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, '..', 'chk.py')).read().split('codes=')[0])  # ref(t, op)

PROBES = ['S0','S1','S2','CP','EP','nLM','nCE','nLI','nEI','nLA','EA','SU','EU','nLB','nLO']
SIG = {'Ep':('EP',0),'Cp':('CP',0),'Lm':('nLM',1),'Ce':('nCE',1),'Li':('nLI',1),'Ei':('nEI',1),
       'La':('nLA',1),'Ea':('EA',0),'Su':('SU',0),'Eu':('EU',0),'Lb':('nLB',1),'Lo':('nLO',1)}
SW = {'CLK': 170, 'OP0': 540, 'OP1': 593, 'OP2': 646, 'OP3': 699}
state = {'CLK': 0, 'OP0': 1, 'OP1': 1, 'OP2': 1, 'OP3': 1}

def ui(*a): subprocess.run([os.path.join(D, 'pfront.sh')] + [str(x) for x in a], check=True)
def toggle(name): ui('c', 285, SW[name], 'w', 500); state[name] ^= 1

def read():
    subprocess.run([os.path.join(D, 'winshot.sh'), os.path.join(D, 'raw.png')], capture_output=True)
    im = Image.open(os.path.join(D, 'raw.png')).convert('RGB')
    y = 2164; xs = []
    for x in range(400, 3700):
        r, g, b = im.getpixel((x, y))
        if (r > 90 and g < 40 and b < 40) or (b > 140 and r < 40 and g < 40): xs.append(x)
    boxes = []
    for x in xs:
        if boxes and x - boxes[-1][1] <= 8: boxes[-1][1] = x
        else: boxes.append([x, x])
    boxes = [b for b in boxes if b[1] - b[0] >= 15]
    assert len(boxes) == 15, boxes
    v = {}
    for k, (x0, x1) in enumerate(boxes):
        blue = red = 0
        for x in range(x0, x1 + 1):
            for yy in range(2148, 2180, 2):
                r, g, b = im.getpixel((x, yy))
                if b > 140 and r < 40: blue += 1
                if r > 150 and g < 40 and b < 40: red += 1
        v[PROBES[k]] = 1 if red > blue else 0
    return v

if sys.argv[1:] == ['read']: print(read()); sys.exit()
bad = 0
for op, code in [('LDA', 0), ('ADD', 1), ('SUB', 2), ('OUT', 14), ('HLT', 15)]:
    for i in range(4):
        if state['OP%d' % i] != (code >> i & 1): toggle('OP%d' % i)
    seen = 0
    while seen < 6:
        v = read()
        t = v['S0'] + 2 * v['S1'] + 4 * v['S2'] + 1
        got = {k for k, (n, inv) in SIG.items() if v[n] ^ inv}
        exp = ref(t, op)
        flag = 'OK ' if got == exp else 'BAD'
        if got != exp: bad += 1
        print(f'{flag} {op} T{t}: {sorted(got)}' + ('' if got == exp else f'  expected {sorted(exp)}'), flush=True)
        toggle('CLK'); toggle('CLK')
        seen += 1
print('FAILURES:', bad)
