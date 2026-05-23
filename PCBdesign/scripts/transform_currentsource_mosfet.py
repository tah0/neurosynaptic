#!/usr/bin/env python3
"""Transform Current_Source.kicad_sch: replace ALD1105PBL with discrete MOSFET equivalents.

IC1 → Q_PMOS_CurrentMirror (neuromorphic lib) + Q_NMOS (Device lib)

Pin positions are identical to BJT equivalents so all wires are reused unchanged.
"""

import uuid, re, sys

BASE      = "/home/todd/Documents/Thesis/neuromorphic circuit/neurosynaptic/PCBdesign"
SCH       = f"{BASE}/kicad/CurrentSource/Current_Source.kicad_sch"
NEURO     = f"{BASE}/kicad/lib/neuromorphic.kicad_sym"
DEV       = "/usr/share/kicad/symbols/Device.kicad_sym"
PROJ      = "/393db921-948b-421d-9f4e-64cd36b2089e"
PROJ_NAME = "Current_Source"

def gu(): return str(uuid.uuid4())

with open(SCH)   as f: c     = f.read()
with open(NEURO) as f: neuro = f.read()
with open(DEV)   as f: dev   = f.read()

errors = []

def remove_by_uuid(text, uid, label=""):
    idx = text.find('"' + uid + '"')
    if idx < 0:
        errors.append(f"UUID not found: {uid} ({label})"); return text
    block_start = text.rfind('\n\t(', 0, idx)
    if block_start < 0:
        errors.append(f"Block start not found for {uid} ({label})"); return text
    depth = 0; i = block_start + 1; end = -1
    while i < len(text):
        if text[i] == '(': depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0: end = i; break
        i += 1
    if end < 0:
        errors.append(f"Block end not found for {uid} ({label})"); return text
    print(f"✓ removed: {label}")
    return text[:block_start] + text[end+1:]

def wire(x1, y1, x2, y2):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1} {y1}) (xy {x2} {y2})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(uuid "{gu()}")\n\t)')

def junction(x, y):
    return (f'\t(junction\n\t\t(at {x} {y})\n\t\t(diameter 0)\n'
            f'\t\t(color 0 0 0 0)\n\t\t(uuid "{gu()}")\n\t)')

def _pwr(lib_id, x, y, rot, value, val_offset_y):
    val_y = round(y + val_offset_y, 4)
    return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rot})
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "{gu()}")
\t\t(property "Reference" "#PWR?"
\t\t\t(at {x} {y} 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {x} {val_y} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at {x} {y} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {x} {y} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Description" ""
\t\t\t(at {x} {y} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pin ""
\t\t\t(uuid "{gu()}")
\t\t)
\t\t(instances
\t\t\t(project "{PROJ_NAME}"
\t\t\t\t(path "{PROJ}"
\t\t\t\t\t(reference "#PWR?")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""

def vcc_sym(x, y, rot=0):
    offset = 3.81 if rot == 0 else -3.81
    return _pwr("Current_Source-altium-import:+5V_BAR", x, y, rot, "+5V", offset)

def mosfet(lib_id, cx, cy, rot, ref, value, pin_names):
    if rot == 0:
        rx = round(cx + 5.08, 4); ry_ref = round(cy + 1.27, 4); ry_val = round(cy - 1.27, 4)
    elif rot == 180:
        rx = round(cx - 5.08, 4); ry_ref = round(cy - 1.27, 4); ry_val = round(cy + 1.27, 4)
    else:
        rx = round(cx + 1.27, 4); ry_ref = round(cy - 5.08, 4); ry_val = round(cy + 5.08, 4)
    pin_blocks = '\n'.join(
        f'\t\t(pin "{p}"\n\t\t\t(uuid "{gu()}")\n\t\t)' for p in pin_names)
    return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {cx} {cy} {rot})
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "{gu()}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {rx} {ry_ref} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {rx} {ry_val} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at {cx} {cy} 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {cx} {cy} 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Description" ""
\t\t\t(at {cx} {cy} 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
{pin_blocks}
\t\t(instances
\t\t\t(project "{PROJ_NAME}"
\t\t\t\t(path "{PROJ}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: lib_symbols – remove ALD1105PBL, add Q_NMOS and Q_PMOS_CurrentMirror
# ══════════════════════════════════════════════════════════════════════════════

ald_match = re.search(r'\t\t\(symbol "\*:root_2_ALD1105PBL_\*".*?\(embedded_fonts no\)\n\t\t\)',
                      c, re.DOTALL)
if not ald_match:
    errors.append("ALD1105PBL lib symbol not found"); sys.exit(1)

def extract_dev_sym(name):
    idx = dev.find(f'\n\t(symbol "{name}"\n')
    idx_next = dev.find('\n\t(symbol "', idx + len(name) + 20)
    raw = dev[idx+1:idx_next]
    lines = raw.split('\n')
    shifted = '\n'.join('\t' + l if l else '' for l in lines)
    shifted = shifted.replace(f'\t\t(symbol "{name}"', f'\t\t(symbol "Device:{name}"', 1)
    return shifted

def extract_neuro_sym(name):
    idx = neuro.find(f'\n\t(symbol "{name}"\n')
    idx_next = neuro.find('\n\t(symbol "', idx + len(name) + 20)
    if idx_next < 0:
        idx_next = neuro.rfind('\n)')
    raw = neuro[idx+1:idx_next]
    lines = raw.split('\n')
    shifted = '\n'.join('\t' + l if l else '' for l in lines)
    shifted = shifted.replace(f'\t\t(symbol "{name}"', f'\t\t(symbol "neuromorphic:{name}"', 1)
    return shifted

q_nmos_lib    = extract_dev_sym('Q_NMOS')
q_pmos_cm_lib = extract_neuro_sym('Q_PMOS_CurrentMirror')

new_lib = q_nmos_lib + '\n' + q_pmos_cm_lib
c = c[:ald_match.start()] + new_lib + c[ald_match.end():]
print("✓ lib_symbols: replaced ALD1105PBL with Device:Q_NMOS + neuromorphic:Q_PMOS_CurrentMirror")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: Remove IC1 ALD1105PBL instance
# ══════════════════════════════════════════════════════════════════════════════

c = remove_by_uuid(c, "30f222c9-9166-4e4e-9293-23f739c63cdc", "IC1 ALD1105PBL")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Remove 4 junctions
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("137732b3-1b82-45ad-9b58-a465fd0e738f", "junction (152.4,108.4072)"),
    ("49d61e0e-c100-4be6-98f5-7341fff5ebfe", "junction (177.8,108.4072)"),
    ("9fa06e00-52ca-4ae2-8758-767ede02e4d6", "junction (152.4,110.9472)"),
    ("ac1bbf8d-249a-4b1f-8384-72259b6cbc6b", "junction (165.1,110.9472)"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Remove 18 wires
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("6c50b13f-d995-4fa2-9c2c-42211c717261", "wire SP1→SP bus (177.8,108.4072)↔(177.8,103.3272)"),
    ("d2ee25f5-8399-4e2e-a844-66f2f3eeeccf", "wire SP1 stub (177.8,108.4072)↔(175.26,108.4072)"),
    ("e36c7273-2267-461a-af7a-ba4fa37e2615", "wire GP1→gate bus (177.8,110.9472)↔(165.1,110.9472)"),
    ("2cdd8010-9f91-4c32-995a-c465a368bea3", "wire J2→DP1 (190.5,113.4872)↔(177.8,113.4872)"),
    ("bc9ddc86-84e7-4994-a5fd-1def764011c1", "wire V- pin (182.88,116.0272)↔(177.8,116.0272)"),
    ("502e5245-84b2-4754-b6a1-60ceab20ded7", "wire V- routing (182.88,128.7272)↔(182.88,116.0272)"),
    ("d9018b7a-d9bd-4134-8cbd-efe01ea8c934", "wire GND→V- path (152.4,128.7272)↔(182.88,128.7272)"),
    ("5d57c25b-dc29-4bbb-b9c9-da9fcbe0de8f", "wire SP bus (177.8,103.3272)↔(152.4,103.3272)"),
    ("1ee88a30-6560-424a-8b5b-6f16aace18b5", "wire gate bus seg (165.1,110.9472)↔(152.4,110.9472)"),
    ("b01902cc-5b7c-48e0-887e-02c9b1db46d8", "wire GP2→R1 (152.4,110.9472)↔(147.32,110.9472)"),
    ("bc1d9820-df1c-493c-a1b9-5aab462f54e7", "wire SP2 bus→SP2 (152.4,103.3272)↔(152.4,108.4072)"),
    ("48f8c34e-6a09-40fb-be8e-e1cdc349c907", "wire SP2→GP2 bus (152.4,108.4072)↔(152.4,110.9472)"),
    ("1bb22b2d-5522-4799-9176-6d19482c3f2a", "wire gate bus→V+ (165.1,110.9472)↔(165.1,116.0272)"),
    ("3501bce7-ece4-4b04-9df4-229f453124d9", "wire V+ pin (165.1,116.0272)↔(152.4,116.0272)"),
    ("49533f52-c0f9-4cdd-84a1-b5d6de740a2b", "wire DP2 pin (142.24,113.4872)↔(152.4,113.4872)"),
    ("44545270-083e-4a50-9a5d-42480e34315a", "wire SN2 pin (142.24,118.5672)↔(152.4,118.5672)"),
    ("dffeddf2-1385-41ba-97da-8340dae4de4d", "wire GN2 pin (144.78,121.1072)↔(152.4,121.1072)"),
    ("9b4e34d5-c59e-4d9e-962c-571e69b627c4", "wire DN2→GND (152.4,123.6472)↔(152.4,128.7272)"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: Build and insert new symbols + wires
# ══════════════════════════════════════════════════════════════════════════════

# Same positions as BJT equivalents (pin positions are identical)
q1     = mosfet("neuromorphic:Q_PMOS_CurrentMirror", 165.1,  108.4072, 0, "Q1", "DMP2110UVTQ-7", ["S1","S2","D1","D2"])
q2     = mosfet("Device:Q_NMOS",                     149.86, 121.1072, 0, "Q2", "DMN2041UVT-7",  ["G","D","S"])
vcc_s1 = vcc_sym(170.18, 103.3272)   # S1 of Q1
vcc_s2 = vcc_sym(160.02, 103.3272)   # S2 of Q1

new_elements = '\n'.join([
    wire(170.18, 113.4872, 190.5,  113.4872),   # Q1 D1 → J2 input
    wire(160.02, 113.4872, 142.24, 113.4872),   # Q1 D2 → output column
    wire(152.4,  116.0272, 152.4,  118.5672),   # Q2 D down
    wire(152.4,  118.5672, 142.24, 118.5672),   # Q2 D → output node
    wire(152.4,  126.1872, 152.4,  128.7272),   # Q2 S → GND junction
])

new_syms = '\n'.join([q1, q2, vcc_s1, vcc_s2])

if c.rstrip().endswith(')'):
    last_nl = c.rfind('\n)')
    c = c[:last_nl] + '\n' + new_elements + '\n' + new_syms + '\n)'
    if c[-1] != '\n': c += '\n'
    print("✓ added Q1/Q2 MOSFETs, 5 wires, 2 +5V symbols")
else:
    errors.append("Could not locate file closing paren")

# ══════════════════════════════════════════════════════════════════════════════
# Verify paren balance and save
# ══════════════════════════════════════════════════════════════════════════════

opens  = c.count('(')
closes = c.count(')')
if opens != closes:
    errors.append(f"Paren imbalance: {opens} opens vs {closes} closes")

if errors:
    print(f"\n⚠  {len(errors)} ERROR(S):")
    for e in errors: print(f"  - {e}")
    sys.exit(1)

with open(SCH, 'w') as f:
    f.write(c)
print(f"\n✓ Current_Source.kicad_sch written ({len(c)} chars)")
print(f"  Paren balance: {opens} = {closes} ✓")
