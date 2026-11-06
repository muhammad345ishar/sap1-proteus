# SAP-1 in Proteus — build guide

Malvino SAP-1: 8-bit W bus, 4-bit PC/MAR, 16-byte memory, 5 instructions (LDA, ADD, SUB, OUT, HLT), 6 T-states.

**Two simplifications for Proteus:**
1. **Memory is a 2764 EPROM loaded from `PROGRAM_ROM.BIN`** instead of switch-programmed RAM. To change the program, edit `PROGRAM` in `make_roms.py`, run `python3 make_roms.py`, and reload.
2. **The controller-sequencer is microcoded** with two 2764 EPROMs (`CONTROL_ROM1/2.BIN`) plus a step counter, instead of a hard-wired ring counter and gate matrix. It produces the same 12 control signals plus HLT.

The test program computes 16 + 20 + 24 − 32 = **28 = 0x1C**, so the output LEDs should show **0001 1100** and the clock stops. (I checked this with a clock-level simulation of this exact wiring: it halts after 33 clocks with OUT = 0x1C.)

---

## How to wire it fast: use net labels

Don't draw long wires. In Proteus, **any two wires with the same label are connected**. Draw a short wire stub on each pin, then use the **Wire Label** tool (the `LBL` icon) to name it, e.g. `W3` or `nLA`. Every table below just says which label goes on which pin.

- `VCC` = POWER terminal, `GND` = GROUND terminal (Terminals Mode → POWER / GROUND).
- Chip VCC/GND pins are hidden in Proteus and connect automatically.
- An `n` prefix means active-low (for example `nLA` = L̄a).

## Parts list (Pick Devices, keyword search)

| Ref | Part | Job |
|---|---|---|
| U1 | 74LS161 | Program counter |
| U2 | 74LS245 | PC → bus (Ep) |
| U3 | 74LS173 | MAR |
| U4 | 2764 | Memory (program ROM) |
| U5, U6 | 74LS173 | IR high (opcode), IR low (operand → bus) |
| U7, U8 | 74LS173 | Accumulator low / high |
| U9 | 74LS245 | A → bus (Ea) |
| U10, U11 | 74LS173 | B register low / high |
| U12, U13 | 74LS86 | XOR (subtract) |
| U14, U15 | 74LS283 | Adder low / high |
| U16 | 74LS245 | Adder → bus (Eu) |
| U17, U18 | 74LS173 | Output register low / high |
| U19 | 74LS161 | T-state (step) counter |
| U20, U21 | 2764 | Control ROM 1 / 2 |
| U22 | 74LS08 | AND gates |
| U23 | 74LS04 | Inverters |
| U24 | 74LS00 | NAND gate |
| — | DCLOCK generator | Clock (Generator Mode → DCLOCK, set to **2 Hz** to watch it) |
| — | BUTTON + 10 kΩ RES | Reset (pull-up to VCC, button to GND) |
| — | 8× LED-RED + 330 Ω (or 8× LOGICPROBE) | Binary display |

---

## Glue logic (clock, halt, reset)

| Gate | Inputs | Output label |
|---|---|---|
| 74LS08 gate 1 (pins 1, 2 → 3) | `CLK` (from DCLOCK), `nHLT` | `CLKG` (gated clock) |
| 74LS04 gate 1 (1 → 2) | `CLKG` | `nCLKG` |
| 74LS04 gate 2 (3 → 4) | `nRESET` | `RESET` |
| 74LS00 gate 1 (1, 2 → 3) | `S1`, `S2` | `nSTEP6` |
| 74LS08 gate 2 (4, 5 → 6) | `nSTEP6`, `nRESET` | `nCLRSTEP` |

Reset button: 10 kΩ from VCC to the button; that node is `nRESET`. The other side of the button goes to GND.

**Timing:** registers load on the **rising** edge of `CLKG`. The step counter runs on `nCLKG`, so control signals change on the **falling** edge, the same as Malvino's design.

---

## Pinouts you'll need

**74LS173:** 1 M · 2 N · 3 1Q · 4 2Q · 5 3Q · 6 4Q · 7 CLK · 9 G1 · 10 G2 · 11 4D · 12 3D · 13 2D · 14 1D · 15 CLR
(M = N = 0 → outputs on. G1 = G2 = 0 → load on clock. CLR is active-high.)

**74LS161:** 1 CLR̄ · 2 CLK · 3 A · 4 B · 5 C · 6 D · 7 ENP · 9 LOAD̄ · 10 ENT · 11 QD · 12 QC · 13 QB · 14 QA

**74LS245:** 1 DIR · 2–9 A1–A8 · 11–18 B8–B1 · 19 OE̅ (DIR = VCC means A → B)

**74LS283:** 1 Σ2 · 2 B2 · 3 A2 · 4 Σ1 · 5 A1 · 6 B1 · 7 C0 · 9 C4 · 10 Σ4 · 11 B4 · 12 A4 · 13 Σ3 · 14 A3 · 15 B3

**74LS86:** gates (1,2→3) (4,5→6) (9,10→8) (12,13→11)

**2764:** pins are named on the Proteus symbol: A0–A12, D0–D7, CE̅, OE̅, plus VPP and PGM̅ (tie both to VCC).

---

## Block-by-block wiring

### 1. Program counter: U1 (74LS161) + U2 (74LS245)
| U1 pin | Label | | U2 pin | Label |
|---|---|---|---|---|
| CLR̄ | `nRESET` | | A1–A4 | `PC0`–`PC3` |
| CLK | `CLKG` | | A5–A8 | GND |
| ENP, ENT | `CP` | | B1–B8 | `W0`–`W7` |
| LOAD̄ | VCC | | DIR | VCC |
| A, B, C, D | GND | | OE̅ | `nEP` |
| QA–QD | `PC0`–`PC3` | | | |

### 2. MAR: U3 (74LS173)
1D–4D = `W0`–`W3` · 1Q–4Q = `MA0`–`MA3` · G1, G2 = `nLM` · M, N = GND · CLK = `CLKG` · CLR = `RESET`

### 3. Memory: U4 (2764, program ROM)
A0–A3 = `MA0`–`MA3` · A4–A12 = GND · D0–D7 = `W0`–`W7` · CE̅ = GND · **OE̅ = `nCE`** · VPP, PGM̅ = VCC
Double-click → **Image File** = `PROGRAM_ROM.BIN`

### 4. Instruction register: U5 (high), U6 (low)
| | U5 (opcode) | U6 (operand) |
|---|---|---|
| 1D–4D | `W4`–`W7` | `W0`–`W3` |
| 1Q–4Q | `OP0`–`OP3` | `W0`–`W3` |
| G1, G2 | `nLI` | `nLI` |
| M, N | GND | **`nEI`** |
| CLK / CLR | `CLKG` / `RESET` | `CLKG` / `RESET` |

### 5. Accumulator: U7 (low), U8 (high), U9 (245)
U7: 1D–4D = `W0`–`W3`, 1Q–4Q = `A0`–`A3` · U8: 1D–4D = `W4`–`W7`, 1Q–4Q = `A4`–`A7`
Both: G1, G2 = `nLA` · M, N = GND · CLK = `CLKG` · CLR = `RESET`
U9: A1–A8 = `A0`–`A7` · B1–B8 = `W0`–`W7` · DIR = VCC · OE̅ = `nEA`

### 6. B register: U10 (low), U11 (high)
Same as the accumulator, but the outputs are `B0`–`B7` and G1, G2 = `nLB`.

### 7. Adder/subtractor: U12, U13 (XOR), U14, U15 (283), U16 (245)
- **XOR:** each `Bn` XOR `SU` → `XBn` (U12 does B0–B3, U13 does B4–B7). One input of every gate goes to `SU`.
- **U14 (low):** A1–A4 = `A0`–`A3` · B1–B4 = `XB0`–`XB3` · **C0 = `SU`** · Σ1–Σ4 = `SUM0`–`SUM3` (not `S0`…, which is the step counter) · C4 = `CARRY`
- **U15 (high):** A1–A4 = `A4`–`A7` · B1–B4 = `XB4`–`XB7` · C0 = `CARRY` · Σ1–Σ4 = `SUM4`–`SUM7`
- **U16:** A1–A8 = `SUM0`–`SUM7` · B1–B8 = `W0`–`W7` · DIR = VCC · OE̅ = `nEU`

(SU = 1 inverts B and adds 1, which is two's-complement subtraction: A − B.)

### 8. Output register: U17 (low), U18 (high)
1D–4D = `W0`–`W3` / `W4`–`W7` · 1Q–4Q = `OUT0`–`OUT7` · G1, G2 = `nLO` · M, N = GND · CLK = `CLKG` · CLR = `RESET`
Each `OUTn` → LED (+ 330 Ω to GND), or a LOGICPROBE. `OUT7` is the left-most LED.

### 9. Controller-sequencer: U19 (step counter) + U20, U21 (control ROMs)
**U19 (74LS161):** CLK = `nCLKG` · CLR̄ = `nCLRSTEP` · ENP, ENT, LOAD̄ = VCC · A–D = GND · QA = `S0`, QB = `S1`, QC = `S2`
(It counts 0–5 for T1–T6; at 6 the NAND clears it back to 0.)

**U20 and U21 (2764), the same address wiring on both:**
A0 = `S0` · A1 = `S1` · A2 = `S2` · A3 = `OP0` · A4 = `OP1` · A5 = `OP2` · A6 = `OP3` · A7–A12 = GND · CE̅ = OE̅ = GND · VPP, PGM̅ = VCC

| Data pin | U20 (`CONTROL_ROM1.BIN`) | U21 (`CONTROL_ROM2.BIN`) |
|---|---|---|
| D0 | `nHLT` | `nEA` |
| D1 | `CP` | `SU` |
| D2 | `nEP` | `nEU` |
| D3 | `nLM` | `nLB` |
| D4 | `nCE` | `nLO` |
| D5 | `nLI` | — |
| D6 | `nEI` | — |
| D7 | `nLA` | — |

The ROMs store real pin levels. Malvino's Ep, Ea and Eu are active-high, but here they come out already inverted (`nEP`, `nEA`, `nEU`) so they can drive the 245 OE̅ pins directly, with no extra inverters.

---

## Microcode (what's in the control ROMs)

| T-state | Signals active |
|---|---|
| T1 | Ep, L̄m (address state) |
| T2 | Cp (increment) |
| T3 | C̄E, L̄i (memory state) |

| Opcode | T4 | T5 | T6 |
|---|---|---|---|
| LDA 0000 | L̄m, Ēi | C̄E, L̄a | — |
| ADD 0001 | L̄m, Ēi | C̄E, L̄b | L̄a, Eu |
| SUB 0010 | L̄m, Ēi | C̄E, L̄b | L̄a, Su, Eu |
| OUT 1110 | Ea, L̄o | — | — |
| HLT 1111 | HLT (stops the clock) | | |

## Test program (`PROGRAM_ROM.BIN`)

| Addr | Hex | Instruction |
|---|---|---|
| 0 | 09 | LDA 9 |
| 1 | 1A | ADD A |
| 2 | 1B | ADD B |
| 3 | 2C | SUB C |
| 4 | E0 | OUT |
| 5 | F0 | HLT |
| 9 / A / B / C | 10 / 14 / 18 / 20 | data: 16, 20, 24, 32 |

---

## Running it
1. Load the three image files into U4, U20 and U21 (double-click → Image File).
2. Press ▶. Click the reset button once.
3. At 2 Hz it takes about 17 seconds. The LEDs should end at **0001 1100** and the clock should stop.

**If it doesn't work, check these first:**
- **The output is wrong.** Check the order of `OP0`–`OP3` and `S0`–`S2` on the control ROM address pins. Swapped bits are the most common mistake.
- **Grey or yellow bus lines** mean that net is floating or has a conflict. A floating bus during T2/T6 is normal, because nothing is driving it then.
- **The clock never stops.** `nHLT` isn't reaching the 74LS08, or U21/U20 got each other's image files.
