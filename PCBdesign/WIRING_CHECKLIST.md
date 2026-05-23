# Breadboard Wiring Checklist — BJT Adaptation

Generated from KiCad BJT branch schematics.

Pin notation: `Ref.Pin` — tick each [ ] as you wire it.

⚠ Some Current Source nets incomplete (dangling wires in original Altium import).
  Verify missing connections visually in KiCad before building.


---
## SYNAPSE LPS (Delta + CM1 + CM2)

### Bill of Materials

| Ref | Value | Notes |
|-----|-------|-------|
| **C1** | Cap Semi |  |
| **C2** | Cap2 |  |
| **C3** | Cap Semi |  |
| **C4** | Cap2 |  |
| | | |
| **J1** | SSW-102-01-G-S | 2-pin header |
| **J2** | SSW-102-01-G-S | 2-pin header |
| **J3** | TSW-102-07-G-S | 2-pin header |
| **J4** | TSW-102-07-G-S | 2-pin header |
| | | |
| **P1** | TSW-102-07-G-S | 2-pin header |
| **P2** | TSW-102-07-G-S | 2-pin header |
| **P3** | TSW-102-07-G-S | 2-pin header |
| **P4** | TSW-102-07-G-S | 2-pin header |
| | | |
| **Q1** | BC547 | BC547=NPN(matched), BC557=PNP(matched) |
| **Q2** | BC557 | BC547=NPN(matched), BC557=PNP(matched) |
| **Q3** | BC547 | BC547=NPN(matched), BC557=PNP(matched) |
| **Q4** | BC557 | BC547=NPN(matched), BC557=PNP(matched) |
| **Q5** | BC557 | BC547=NPN(matched), BC557=PNP(matched) |
| **Q6** | BC547 | BC547=NPN(matched), BC557=PNP(matched) |
| **Q7** | BC547 | BC547=NPN(matched), BC557=PNP(matched) |
| **Q8** | BC557 | BC547=NPN(matched), BC557=PNP(matched) |
| | | |
| **R1** | Res3 | see schematic for value |
| **R2** | Res3 | see schematic for value |
| **R3** | Res3 | see schematic for value |
| **R4** | Res3 | see schematic for value |
| **R5** | Res3 | see schematic for value |
| **R6** | Res3 | see schematic for value |
| | | |
| **RC1** | Res3 | see schematic for value |
| **RC2** | Res3 | see schematic for value |
| | | |
| **RD1** | Res3 | see schematic for value |
| **RD2** | Res3 | see schematic for value |
| **RD3** | Res3 | see schematic for value |
| **RD4** | Res3 | see schematic for value |
| | | |
| **RI1** | Res3 | see schematic for value |
| **RI2** | Res3 | see schematic for value |
| | | |
| **Ral1** | Res3 | see schematic for value |
| | | |
| **Rex1** | Res3 | see schematic for value |
| | | |
| **VR1** | 3214X-1-203E | 20kΩ trim pot (Bourns) |
| **VR2** | 3214X-1-203E | 20kΩ trim pot (Bourns) |

### Wiring (net by net)

**+5V** — connect all together:
```
[ ] J4.1
[ ] P1.2
[ ] P2.2
[ ] P3.2
[ ] Q2.E1
[ ] Q2.E2
[ ] Q4.E1
[ ] Q4.E2
[ ] Q5.E
[ ] Q8.E1
[ ] Q8.E2
[ ] RD1.1
[ ] VR2.3
```

**DEL** — connect all together:
```
[ ] R1.1
[ ] Rex1.2
[ ] VR1.3
```

**Voltage_IN** — connect all together:
```
[ ] P4.2
[ ] RD3.2
[ ] VR1.1
[ ] VR1.2
```

**INP** — connect all together:
```
[ ] C1.2
[ ] C2.1
[ ] RC1.1
[ ] Rex1.1
```

**OUT-E** — connect all together:
```
[ ] Q2.C1
[ ] R3.1
[ ] Ral1.2
```

**OUT-IN** — connect all together:
```
[ ] R2.1
[ ] RI1.1
```

**INP** — connect all together:
```
[ ] C3.2
[ ] C4.1
[ ] RC2.1
[ ] Ral1.1
```

**OUT-E** — connect all together:
```
[ ] Q4.C1
[ ] R5.1
```

**OUT-IN** — connect all together:
```
[ ] R4.1
[ ] RI2.1
```

**IN** — connect all together:
```
[ ] J1.2
[ ] RD2.1
```

**OUT** — connect all together:
```
[ ] J2.2
[ ] R1.2
[ ] R2.2
[ ] R3.2
[ ] R4.2
[ ] R5.2
```

**GND** — connect all together:
```
[ ] C1.1
[ ] C2.2
[ ] C3.1
[ ] C4.2
[ ] J1.1
[ ] J2.1
[ ] J3.1
[ ] J4.2
[ ] P1.1
[ ] P2.1
[ ] P3.1
[ ] P4.1
[ ] Q1.E1
[ ] Q1.E2
[ ] Q3.E
[ ] Q6.E1
[ ] Q6.E2
[ ] Q7.E1
[ ] Q7.E2
[ ] RD4.1
```


---
## CURRENT SOURCE

### Bill of Materials

| Ref | Value | Notes |
|-----|-------|-------|
| **D1** | P0118MA_2AL3 | SCR — pins: 1=K(Kathode), 2=G(Gate), 3=A(Anode) |
| | | |
| **J1** | TSW-102-07-G-S | 2-pin header — pin1=+5V, pin2=GND |
| **J2** | TSW-102-07-G-S | 2-pin header — pin1=OUT, pin2=GND |
| | | |
| **Q1** | BC557 | PNP current mirror (matched pair) |
| **Q2** | BC547 | NPN (matched) |
| | | |
| **R1** | 100 kΩ | |
| **R2** | 100 kΩ | |
| | | |
| **VR1** | 3214X-1-203E | 20kΩ trim pot (Bourns) |

### Notes on resistor values

| Ref | Value (from original Altium schematic) |
|-----|---------------------------------------|
| **R1** | 100 kΩ |
| **R2** | 100 kΩ |
| **VR1** | 20 kΩ trim pot (Bourns 3214X-1-203E) |

⚠ **R1.2 dangling** — R1 pin 2 (end away from +5V) has no wire in the KiCad import.
  In the original Altium schematic this pin connected to the internal base bus of Q1 (the
  Q_PNP_CurrentMirror symbol has a graphical base node but no netlist pin). When building,
  connect R1.2 to the shared base node of Q1 — the junction on Q1's body between the two
  collectors (see schematic for visual reference).

⚠ **+5V vs +5** — two distinct supply labels exist in this schematic:
  - `+5V` — main supply rail (used by J1.1, Q1.E1/E2, R1.1)
  - `+5` — gate-bias rail for D1 (used by D1.G). May be the same physical supply or a
    lower-voltage rail — verify in the original design intent before wiring.

### Wiring (net by net)

**+5V** — connect all together:
```
[ ] J1.1
[ ] Q1.E1
[ ] Q1.E2
[ ] R1.1
```

**GND** — connect all together:
```
[ ] D1.K  (D1 pin 1 — Kathode)
[ ] J1.2
[ ] J2.2
[ ] Q2.E
```

**OUT** — current output, connect all together:
```
[ ] J2.1
[ ] Q1.C1
```

**BIAS** — Q1 feedback / Q2 collector bus, connect all together:
```
[ ] Q1.C2
[ ] Q2.C
[ ] VR1.1  (CCW end of trim pot)
[ ] VR1.2  (WIPER of trim pot)
[ ] R2.2
```

**VR1–R2** — trim-pot CW end to resistor, connect together:
```
[ ] VR1.3  (CW end of trim pot)
[ ] R2.1
```

**Q2B–D1A** — Q2 base driven by SCR anode, connect together:
```
[ ] Q2.B
[ ] D1.A  (D1 pin 3 — Anode)
```

**+5 (gate bias)** — D1 gate supply:
```
[ ] D1.G  (D1 pin 2 — Gate)  →  +5 supply rail
```

