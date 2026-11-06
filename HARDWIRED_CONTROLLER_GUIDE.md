# SAP-1 hard-wired controller: 2× 74LS154 + NAND only

This replaces the two control ROMs (U20, U21) with:
- 2× **74LS154** (4-to-16 decoder, active-low outputs)
- 7× **74LS00** (quad 2-input NAND), the only gate type used

The step counter (U19, 74LS161, `S0`–`S2`) and the clock, halt and reset glue logic stay as they are.
Every connection is a **net label**, so part reference numbers don't matter.

## Setup
1. Open `SAP1.pdsprj` → **File → Save Project As** → `SAP1_hardwired.pdsprj` (keeps the ROM version safe).
2. Delete U20 and U21 (their stubs and labels go with them).
3. Pick Devices: search `154` (74154 / 74LS154) and `74LS00`.

## Boolean equations (Malvino polarity)
Opcode decoder: LDA = Y0, ADD = Y1, SUB = Y2, OUT = Y14, HLT = Y15. T decoder: T1–T6 = Y0–Y5.

| Signal | Equation |
|---|---|
| Cp | T2 |
| Ep | T1 |
| L̄M | (T1 + T4·(LDA+ADD+SUB))′ |
| C̄E | (T3 + T5·(LDA+ADD+SUB))′ |
| L̄I | T3′ |
| ĒI | (T4·(LDA+ADD+SUB))′ |
| L̄A | (T5·LDA + T6·(ADD+SUB))′ |
| EA | T4·OUT |
| Su | T6·SUB |
| EU | T6·(ADD+SUB) |
| L̄B | (T5·(ADD+SUB))′ |
| L̄O | (T4·OUT)′ |

NAND tricks: decoder outputs are active-low, so NAND(Ȳ1, Ȳ2) = ADD+SUB with one gate,
and an OR of terms is NAND of the inverted terms. A NAND with both inputs tied together is the inverter.

## DEC-T (74LS154): T-state decoder
| Pin | Label |
|---|---|
| A (23) | `S0` |
| B (22) | `S1` |
| C (21) | `S2` |
| D (20) | GND |
| E1/G1 (18), E2/G2 (19) | GND |
| Y0 (1) | `nEP` (= T̄1, drives the PC buffer directly) |
| Y1 (2) | `nT2` |
| Y2 (3) | `nLI` (= T̄3) |
| Y3 (4) | `nT4` |
| Y4 (5) | `nT5` |
| Y5 (6) | `nT6` |

## DEC-OP (74LS154): instruction decoder
| Pin | Label |
|---|---|
| A (23) | `OP0` |
| B (22) | `OP1` |
| C (21) | `OP2` |
| D (20) | `OP3` |
| E1 (18), E2 (19) | GND |
| Y0 (1) | `nLDA` |
| Y1 (2) | `nADD` |
| Y2 (3) | `nSUB` |
| Y14 (16) | `nOUT` |
| Y15 (17) | `nHLT` (goes straight to the clock-gating AND) |

## NAND gates (74LS00: A = 1,2→3 · B = 4,5→6 · C = 9,10→8 · D = 12,13→11)

| Chip | Gate | Input 1 | Input 2 | Output |
|---|---|---|---|---|
| N1 | A | `nT2` | `nT2` | `CP` |
| N1 | B | `nT4` | `nT4` | `T4` |
| N1 | C | `nT5` | `nT5` | `T5` |
| N1 | D | `nT6` | `nT6` | `T6` |
| N2 | A | `nLDA` | `nLDA` | `ILDA` |
| N2 | B | `nSUB` | `nSUB` | `ISUB` |
| N2 | C | `nOUT` | `nOUT` | `IOUT` |
| N2 | D | `nADD` | `nSUB` | `ADDSUB` |
| N3 | A | `ADDSUB` | `ADDSUB` | `nADDSUB` |
| N3 | B | `nLDA` | `nADDSUB` | `MEMREF` (LDA+ADD+SUB) |
| N3 | C | `T4` | `MEMREF` | `nEI` |
| N3 | D | `nEP` | `nEI` | `LM` |
| N4 | A | `LM` | `LM` | `nLM` |
| N4 | B | `T5` | `MEMREF` | `T5MEM` |
| N4 | C | `nLI` | `T5MEM` | `CE` |
| N4 | D | `CE` | `CE` | `nCE` |
| N5 | A | `T5` | `ILDA` | `T5LDA` |
| N5 | B | `T6` | `ADDSUB` | `nEU` |
| N5 | C | `T5LDA` | `nEU` | `LA` |
| N5 | D | `LA` | `LA` | `nLA` |
| N6 | A | `T5` | `ADDSUB` | `nLB` |
| N6 | B | `T4` | `IOUT` | `nLO` |
| N6 | C | `nLO` | `nLO` | `EA` |
| N6 | D | `EA` | `EA` | `nEA` |
| N7 | A | `T6` | `ISUB` | `nSU6` |
| N7 | B | `nSU6` | `nSU6` | `SU` |
| N7 | C, D | spare | | |

26 gates total. For a standalone Malvino-polarity version, add Ep = NAND(`nEP`,`nEP`) and EU = NAND(`nEU`,`nEU`) (27 gates; Ea = N6C already).

## Test
Run with the same `PROGRAM_ROM.BIN`. The output LEDs should end at **0001 1100 (0x1C)** and the clock should stop.
HLT now stops the clock as soon as the HLT opcode lands in the IR (during T3). That's harmless.
