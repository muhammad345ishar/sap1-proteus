"""Generate SAP-1 ROM images for Proteus (2764 EPROMs).

Control ROM address: A0-A2 = step (T1..T6 = 0..5), A3-A6 = opcode.
Values are the real pin levels (active-low signals stored as 0 when active).
Edit PROGRAM below and re-run to change what SAP-1 runs.
"""

# ---- program memory (16 bytes) : Malvino's example ----
PROGRAM = {
    0x0: 0x09,  # LDA 9
    0x1: 0x1A,  # ADD A
    0x2: 0x1B,  # ADD B
    0x3: 0x2C,  # SUB C
    0x4: 0xE0,  # OUT
    0x5: 0xF0,  # HLT
    0x9: 0x10,  # 16
    0xA: 0x14,  # 20
    0xB: 18,  # 18
    0xC: 31,    # 31   -> 16+20+18-31 = 29 = 0x1D
}

# control bits: (rom, bit, active_low)
SIG = {
    "HLT": (1, 0, True), "CP": (1, 1, False), "EP": (1, 2, True), "LM": (1, 3, True),
    "CE": (1, 4, True),  "LI": (1, 5, True),  "EI": (1, 6, True), "LA": (1, 7, True),
    "EA": (2, 0, True),  "SU": (2, 1, False), "EU": (2, 2, True), "LB": (2, 3, True),
    "LO": (2, 4, True),
}

FETCH = [["EP", "LM"], ["CP"], ["CE", "LI"]]
OPS = {
    0x0: [["LM", "EI"], ["CE", "LA"], []],               # LDA
    0x1: [["LM", "EI"], ["CE", "LB"], ["LA", "EU"]],     # ADD
    0x2: [["LM", "EI"], ["CE", "LB"], ["LA", "SU", "EU"]],  # SUB
    0xE: [["EA", "LO"], [], []],                         # OUT
    0xF: [["HLT"], [], []],                              # HLT
}

def word(active):
    r = {1: 0, 2: 0}
    for name, (rom, bit, low) in SIG.items():
        on = name in active
        if on != low:          # level is 1 when (active-high and on) or (active-low and off)
            r[rom] |= 1 << bit
    return r

SIZE = 8192
rom1 = bytearray(SIZE); rom2 = bytearray(SIZE)
idle = word([])
for a in range(SIZE):
    rom1[a], rom2[a] = idle[1], idle[2]
for op in range(16):
    steps = FETCH + OPS.get(op, [[], [], []])
    for t in range(8):
        w = word(steps[t]) if t < 6 else idle
        a = (op << 3) | t
        rom1[a], rom2[a] = w[1], w[2]

prog = bytearray(SIZE)
for a, v in PROGRAM.items():
    prog[a] = v

def ihex(data, n):
    lines = []
    for off in range(0, n, 16):
        chunk = data[off:off+16]
        rec = [len(chunk), off >> 8, off & 0xFF, 0] + list(chunk)
        lines.append(":" + "".join(f"{b:02X}" for b in rec) + f"{(-sum(rec)) & 0xFF:02X}")
    lines.append(":00000001FF")
    return "\n".join(lines) + "\n"

for name, data, used in (("CONTROL_ROM1", rom1, 128), ("CONTROL_ROM2", rom2, 128), ("PROGRAM_ROM", prog, 16)):
    open(name + ".BIN", "wb").write(data)
    open(name + ".HEX", "w").write(ihex(data, max(used, 16)))
print("ROM files written")
