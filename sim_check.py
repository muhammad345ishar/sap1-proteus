"""Clock-level check of the SAP-1 wiring using the generated ROM images."""
r1 = open("CONTROL_ROM1.BIN", "rb").read()
r2 = open("CONTROL_ROM2.BIN", "rb").read()
prog = open("PROGRAM_ROM.BIN", "rb").read()

pc = mar = ir = a = b = out = 0
step = 0
for cycle in range(200):
    addr = ((ir >> 4) << 3) | step
    c1, c2 = r1[addr], r2[addr]
    nHLT, CP, nEP, nLM, nCE, nLI, nEI, nLA = [(c1 >> i) & 1 for i in range(8)]
    nEA, SU, nEU, nLB, nLO = [(c2 >> i) & 1 for i in range(5)]
    if not nHLT:
        break
    drivers = []
    if not nEP: drivers.append(pc & 0xF)
    if not nCE: drivers.append(prog[mar])
    if not nEI: drivers.append(ir & 0xF)
    if not nEA: drivers.append(a)
    total = (a + ((b ^ 0xFF) if SU else b) + SU) & 0xFF
    if not nEU: drivers.append(total)
    assert len(drivers) <= 1, f"bus conflict at step {step}"
    bus = drivers[0] if drivers else None
    # rising edge: every register latches at once
    n_pc = (pc + 1) & 0xF if CP else pc
    if not nLM: mar = bus & 0xF
    if not nLI: ir = bus
    if not nLA: a = bus
    if not nLB: b = bus
    if not nLO: out = bus
    pc = n_pc
    # falling edge: step counter, cleared when it reaches 6
    step = (step + 1) % 6
print(f"halted after {cycle} clocks, OUT = 0x{out:02X} = {out:08b}")
