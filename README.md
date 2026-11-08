# SAP-1 in Proteus

Malvino's **Simple-As-Possible (SAP-1)** 8-bit computer, built from 74LS-series chips and simulated in **Proteus 8**, with interactive web pages that show how it works.

**Live site:** https://muhammad345ishar.github.io/sap1-proteus/

## Interactive pages
| Page | What it shows |
|---|---|
| [SAP-1 Bit Flow](https://muhammad345ishar.github.io/sap1-proteus/sap1-bitflow.html) | Each byte travelling the W bus between registers, one T-state at a time |
| [Chip Field Guide](https://muhammad345ishar.github.io/sap1-proteus/sap1-chip-guide.html) | Every non-gate IC with its DIP pinout and a mini simulator |
| [IC Workbench](https://muhammad345ishar.github.io/sap1-proteus/sap1-ic-workbench.html) | Each chip on its own test bench with live internal logic |
| [SAP-1 Lab](https://muhammad345ishar.github.io/sap1-proteus/sap1-lab.html) | Drive the control pins yourself, or let the sequencer run |
| [Controller Sequencer](https://muhammad345ishar.github.io/sap1-proteus/sap1-controller-sequencer.html) | Decoder, step counter and the gate matrix behind the 12 control signals |
| [Modified SAP-1 Explorer](https://muhammad345ishar.github.io/sap1-proteus/modified-sap1-explorer.html) | 1-, 2-, 3- and 4-byte machines: states, address path, control matrix and program trace |
| [Variable-Length SAP-1](https://muhammad345ishar.github.io/sap1-proteus/variable-length-sap1.html) | LEN signal and the T3 → T7 skip in the 9-bit ring counter, with Verilog |
| [SAP-1 Revision Kit](https://muhammad345ishar.github.io/sap1-proteus/sap1-revision-kit.html) | Hardware bench widgets, revision tables and a quiz |

## Exam solutions
| Page | What it covers |
|---|---|
| [DLD Terminal 2025, Solved](https://muhammad345ishar.github.io/sap1-proteus/dld-terminal-2025.html) | Worked answers to the 1 Jan 2025 Digital Logic Design terminal paper, with diagrams |

## Topic guides
| Page | What it covers |
|---|---|
| [8051 Memory Interfacing](https://muhammad345ishar.github.io/sap1-proteus/8051-memory-interfacing.html) | Decoders and chip selects from first principles, the Block Method, all past-paper chip-select questions solved, and an interactive solver |

## The machine
- 8-bit W bus, 4-bit program counter and MAR, 16 bytes of memory
- 5 instructions: `LDA`, `ADD`, `SUB`, `OUT`, `HLT`, with 6 T-states each
- Memory is a 2764 EPROM loaded from `PROGRAM_ROM.BIN`
- Controller: microcoded (two 2764 control ROMs plus a 74LS161 step counter), or the hard-wired version (74LS154 decoders plus NAND gates)

The default program computes `16 + 20 + 18 − 31 = 23` and shows `0001 0111` on the output probes.

## Files
| Path | Contents |
|---|---|
| `proteus/SAP1.pdsprj` | Microcoded SAP-1 (control ROMs) |
| `proteus/SAP1_Controller_wired.pdsprj` | Hard-wired controller version |
| `SAP1_PROTEUS_GUIDE.md` | Build guide: parts, pinouts, net labels, microcode |
| `HARDWIRED_CONTROLLER_GUIDE.md` | Hard-wired controller equations and wiring |
| `make_roms.py` | Generates `PROGRAM_ROM.BIN` and `CONTROL_ROM1/2.BIN` |
| `sim_*.py`, `ctrl_plan.py`, `rail_plan.py`, `render_wiring.py` | Clock-level checks and wiring-diagram helpers |

## Running a different program
1. Edit `PROGRAM` in `make_roms.py`. The high hex digit is the opcode (`0` LDA, `1` ADD, `2` SUB, `E` OUT, `F` HLT) and the low digit is the address.
2. Run `python3 make_roms.py`.
3. In Proteus, stop the simulation and start it again, then set the reset toggle to 1.

> **ROM paths:** the 2764 parts point to `C:\users\<you>\Documents\SAP1 Proteus\*.BIN`. If you clone this repo somewhere else, double-click U4, U20 and U21 and update **Image File**.

