#!/usr/bin/env python3
"""Transform Current Mirror_1.kicad_sch: replace ALD1105PBL with discrete MOSFET equivalents.

ALD (*:1_0_ALD1105PBL_*) → Q_NMOS_CurrentMirror + Q_PMOS_CurrentMirror (neuromorphic lib)
Pin positions identical to BJT equivalents; all wires reused unchanged.
"""

import uuid, re, sys

BASE      = "/home/todd/Documents/Thesis/neuromorphic circuit/neurosynaptic/PCBdesign"
SCH       = f'{BASE}/kicad/Synapse/Current Mirror_1.kicad_sch'
NEURO     = f"{BASE}/kicad/lib/neuromorphic.kicad_sym"
DEV       = "/usr/share/kicad/symbols/Device.kicad_sym"
PROJ      = "/af4a7426-c915-4fd8-a9a0-d1d0653890c7/efb34e1f-b4a1-4d0a-a367-85b7a624cd54"
PROJ_NAME = "Synapse_LPS"

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

def gnd_sym(x, y):
    return _pwr("Synapse_LPS-altium-import:GND_POWER_GROUND", x, y, 0, "GND", 6.35)

def vcc_sym(x, y, rot=0):
    offset = 3.81 if rot == 0 else -3.81
    return _pwr("Synapse_LPS-altium-import:+5V_BAR", x, y, rot, "+5V", offset)

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
# STEP 1: lib_symbols – remove ALD1105PBL, add Q_NMOS_CM + Q_PMOS_CM
# ══════════════════════════════════════════════════════════════════════════════

ald_match = re.search(r'\t\t\(symbol "\*:1_0_ALD1105PBL_\*".*?\(embedded_fonts no\)\n\t\t\)',
                      c, re.DOTALL)
if not ald_match:
    errors.append("ALD1105PBL lib symbol not found"); sys.exit(1)

def extract_neuro_sym(name):
    idx = neuro.find(f'\n\t(symbol "{name}"\n')
    idx_next = neuro.find('\n\t(symbol "', idx + len(name) + 20)
    if idx_next < 0: idx_next = neuro.rfind('\n)')
    raw = neuro[idx+1:idx_next]
    lines = raw.split('\n')
    shifted = '\n'.join('\t' + l if l else '' for l in lines)
    shifted = shifted.replace(f'\t\t(symbol "{name}"', f'\t\t(symbol "neuromorphic:{name}"', 1)
    return shifted

q_nmos_cm_lib = extract_neuro_sym('Q_NMOS_CurrentMirror')
q_pmos_cm_lib = extract_neuro_sym('Q_PMOS_CurrentMirror')

new_lib = q_nmos_cm_lib + '\n' + q_pmos_cm_lib
c = c[:ald_match.start()] + new_lib + c[ald_match.end():]
print("✓ lib_symbols: replaced ALD1105PBL with Q_NMOS_CM + Q_PMOS_CM")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: Remove ALD instance
# ══════════════════════════════════════════════════════════════════════════════

c = remove_by_uuid(c, "9b6796db-e2a9-474e-bba1-9cf44321d9ba", "IC1 ALD1105PBL *:1_0*")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Remove junctions
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("30b77a6a-24c8-4bd2-9a0a-0d5dda3cc936", "junction (129.54,102.0572)"),
    ("470bcce6-2fb2-47e4-adc3-a65e5c562523", "junction (154.94,112.2172)"),
    ("641db99c-d99c-421b-947b-dc878e7b29c6", "junction (118.11,104.5972)"),
    ("86d5c2f5-4d2e-478b-b8c9-42f051f66132", "junction (160.02,109.6772)"),
    ("cd674757-4c7a-419e-b319-4699b4ed0bf3", "junction (129.54,96.9772)"),
    ("d6dc6da6-0196-482e-b01c-6df16793e655", "junction (129.54,99.5172)"),
    ("ece1d8dc-488d-4ba7-bb33-66c6f812a844", "junction (165.1,96.9772)"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Remove wires
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("15b1a102-57a6-4bee-ab0e-b54d1b8afe4d", "wire 129.54,118.5672->129.54,112.2172"),
    ("243f5138-1463-4092-8472-a6daefc41505", "wire 149.86,104.5972->144.78,104.5972"),
    ("3e9f79ab-388f-40d7-bc7e-dc8bf03e8346", "wire 129.54,107.1372->121.92,107.1372"),
    ("40c8e323-9637-4d18-929a-393b48965fff", "wire 154.94,107.1372->160.02,107.1372"),
    ("4160835d-f75d-45bb-8bd5-dea513296855", "wire 160.02,104.5972->154.94,104.5972"),
    ("45a91aad-67ec-477b-9388-bf6d562fe483", "wire 154.94,99.5172->129.54,99.5172"),
    ("4da882ad-f1e3-4654-9e0d-d6fcf0b80063", "wire 154.94,102.0572->129.54,102.0572"),
    ("4e10bcbb-8e6d-43eb-83f3-2bb5b1aff652", "wire 144.78,112.2172->154.94,112.2172"),
    ("571e7614-5d97-47f3-9bf9-af627da5641c", "wire 121.92,124.9172->172.72,124.9172"),
    ("620f2e9e-65df-4c3b-bf2b-9c85aaf553f2", "wire 160.02,121.1072->125.73,121.1072"),
    ("625b148e-084a-4b7d-81b7-f3596dd3870a", "wire 154.94,112.2172->154.94,118.5672"),
    ("68ed6cef-b31c-4166-b024-ed0aad8fdbd7", "wire 160.02,109.6772->160.02,121.1072"),
    ("71859ce7-c54f-4d2b-b57d-5a981ae50cbf", "wire 154.94,118.5672->129.54,118.5672"),
    ("761ae949-3998-4cc5-84ba-f4bb78de13d9", "wire 118.11,102.0572->118.11,104.5972"),
    ("7dd42026-b3d7-464d-8ab4-09c7c6e48f99", "wire 129.54,99.5172->129.54,96.9772"),
    ("8c207b40-fe60-469d-9a7f-36df58be46b1", "wire 118.11,104.5972->118.11,131.2672"),
    ("8d4c636f-4a0e-41d7-a09e-1e4dabf396a4", "wire 114.3,96.9772->129.54,96.9772"),
    ("8f176b4e-fe59-48a0-a25a-6a6fef54a535", "wire 125.73,121.1072->125.73,109.6772"),
    ("9841e4f4-b294-4296-8866-dc8467e06323", "wire 125.73,109.6772->129.54,109.6772"),
    ("9ceb3097-6307-436b-88b8-47a2a01faf55", "wire 160.02,109.6772->165.1,109.6772"),
    ("b0a1c248-69a5-4162-b0a2-2228a2881890", "wire 129.54,102.0572->118.11,102.0572"),
    ("c1d040cc-2551-449d-9a87-681e2b33bbb5", "wire 144.78,104.5972->144.78,112.2172"),
    ("cbee5901-3e2b-4b74-a291-105873b6565a", "wire 154.94,109.6772->160.02,109.6772"),
    ("d4db16fc-ccf1-4b7d-860e-e98381631c5a", "wire 165.1,96.9772->172.72,96.9772"),
    ("d91aed9b-85fc-42eb-b95a-7c79d79b362e", "wire 160.02,107.1372->160.02,109.6772"),
    ("db7fc781-b703-47b1-88a9-03734765b188", "wire 154.94,96.9772->165.1,96.9772"),
    ("f27229fc-a6fd-4bea-b05b-c7ed06fd90dc", "wire 129.54,104.5972->118.11,104.5972"),
    ("f58039bd-5d31-4889-95d5-48946419c3e0", "wire 121.92,107.1372->121.92,124.9172"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: Remove old power symbols
# ══════════════════════════════════════════════════════════════════════════════

c = remove_by_uuid(c, "0efd9ff4-c58c-40e5-ab75-ed99fb8047d5", "+5V_BAR at (160.02,104.5972)")
c = remove_by_uuid(c, "a9307744-edc8-4453-8c24-8671491247b1", "GND at (118.11,131.2672)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: Insert new wires, junction, power symbols, and MOSFET instances
# ══════════════════════════════════════════════════════════════════════════════

q_nmos = mosfet("neuromorphic:Q_NMOS_CurrentMirror", 125.73, 114.7572, 0, "Q3", "DMN2041UVT-7", ["D1","D2","S1","S2"])
q_pmos = mosfet("neuromorphic:Q_PMOS_CurrentMirror", 125.73,  99.5172, 0, "Q4", "DMP2110UVTQ-7", ["S1","S2","D1","D2"])

vcc1 = vcc_sym(120.65, 94.4372)
vcc2 = vcc_sym(130.81, 94.4372)
gnd1 = gnd_sym(120.65, 119.8372)
gnd2 = gnd_sym(130.81, 119.8372)

new_elements = '\n'.join([
    wire(114.3,  96.9772, 120.65,  96.9772),
    wire(120.65, 96.9772, 120.65, 104.5972),
    wire(120.65,104.5972, 120.65, 109.6772),
    wire(130.81,109.6772, 165.1,  109.6772),
    wire(165.1,  96.9772, 172.72,  96.9772),
    wire(130.81,104.5972, 155.0,  104.5972),
    wire(155.0, 104.5972, 155.0,  124.9172),
    wire(155.0, 124.9172, 172.72, 124.9172),
    junction(120.65, 104.5972),
])

new_syms = '\n'.join([q_nmos, q_pmos, vcc1, vcc2, gnd1, gnd2])

anchor = '\t(hierarchical_label "INP"'
if anchor in c:
    c = c.replace(anchor, new_elements + '\n' + anchor, 1)
    print("✓ inserted 8 wires + 1 junction")
else:
    errors.append("Anchor 'INP' hierarchical_label not found")

if c.rstrip().endswith(')'):
    last_nl = c.rfind('\n)')
    c = c[:last_nl] + '\n' + new_syms + '\n)'
    if c[-1] != '\n': c += '\n'
    print("✓ added Q3/Q4 MOSFET instances + 4 power symbols")
else:
    errors.append("Could not locate file closing paren")

# ══════════════════════════════════════════════════════════════════════════════
# Verify and save
# ══════════════════════════════════════════════════════════════════════════════

opens = c.count('('); closes = c.count(')')
if opens != closes:
    errors.append(f"Paren imbalance: {opens} vs {closes}")

if errors:
    print(f"\n⚠  {len(errors)} ERROR(S):")
    for e in errors: print(f"  - {e}")
    sys.exit(1)

with open(SCH, 'w') as f: f.write(c)
print(f"\n✓ Current Mirror_1.kicad_sch written ({len(c)} chars, {opens} parens)")
