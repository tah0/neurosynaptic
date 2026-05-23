#!/usr/bin/env python3
"""Transform Delta.kicad_sch: replace ALD1105PBL with discrete MOSFET equivalents.

IC1 → Q_NMOS (single, replaces NPN half) + Q_PMOS (single, replaces PNP half)
IC? → Q_NMOS_CurrentMirror (neuromorphic lib) + Q_PMOS_CurrentMirror (neuromorphic lib)

Pin positions are identical to BJT equivalents so all wires/junctions are reused unchanged.
"""

import uuid, re, sys

BASE   = "/home/todd/Documents/Thesis/neuromorphic circuit/neurosynaptic/PCBdesign"
SCH    = f"{BASE}/kicad/Synapse/Delta.kicad_sch"
NEURO  = f"{BASE}/kicad/lib/neuromorphic.kicad_sym"
DEV    = "/usr/share/kicad/symbols/Device.kicad_sym"
PROJ   = "/af4a7426-c915-4fd8-a9a0-d1d0653890c7/984ef279-a542-4986-b306-8a6747a54659"

def gu(): return str(uuid.uuid4())

with open(SCH)   as f: c    = f.read()
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
\t\t\t(project "Synapse_LPS"
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
\t\t\t(project "Synapse_LPS"
\t\t\t\t(path "{PROJ}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: lib_symbols – remove ALD1105PBL, add Q_NMOS/Q_PMOS/Q_NMOS_CM/Q_PMOS_CM
# ══════════════════════════════════════════════════════════════════════════════

ald_match = re.search(r'\t\t\(symbol "\*:0_0_ALD1105PBL_\*".*?\(embedded_fonts no\)\n\t\t\)',
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
q_pmos_lib    = extract_dev_sym('Q_PMOS')
q_nmos_cm_lib = extract_neuro_sym('Q_NMOS_CurrentMirror')
q_pmos_cm_lib = extract_neuro_sym('Q_PMOS_CurrentMirror')

new_lib = q_nmos_lib + '\n' + q_pmos_lib + '\n' + q_nmos_cm_lib + '\n' + q_pmos_cm_lib
c = c[:ald_match.start()] + new_lib + c[ald_match.end():]
print("✓ lib_symbols: replaced ALD1105PBL with Q_NMOS/Q_PMOS/Q_NMOS_CM/Q_PMOS_CM")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2: Remove junctions
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("0467783c-a394-46a2-9379-b80e8939f530", "junction 228.6,80.4672"),
    ("13686e33-0b5e-4baf-88b9-b499df00517d", "junction 68.58,47.4472"),
    ("2034c63e-6a5c-4fc3-9404-368df52cb42d", "junction 254,90.6272"),
    ("21f41258-3fb0-4f7e-a764-60afc3785b28", "junction 254,95.7072"),
    ("358e656e-e7e2-489e-a5d0-945d6eb37588", "junction 228.6,85.5472"),
    ("3afbba41-579b-4e5b-b44e-ef6f66690551", "junction 241.3,95.7072"),
    ("460d4c18-d8c0-4a1c-b9dd-faaa3aa47959", "junction 254,93.1672"),
    ("86d85c63-2425-460c-949e-f4d8d349d15d", "junction 68.58,52.5272"),
    ("be59ac1a-d331-46b5-a1dc-f49776e15f37", "junction 68.58,57.6072"),
    ("c84049f6-a8d2-4ae9-8c99-d21c0d9fc340", "junction 228.6,83.0072"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Remove wires
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("06e6305c-34e8-45ae-a9c2-f7d60d59f94b", "wire 68.58,52.5272->50.8,52.5272"),
    ("0d50d919-5392-42d8-98f1-ee51eecb2d8f", "wire 259.08,90.6272->254,90.6272"),
    ("11cec70c-7dde-484a-baf7-33b1c5219914", "wire 259.08,80.4672->259.08,90.6272"),
    ("23ae4c33-c76b-4328-b17b-2794b634b2ef", "wire 241.3,95.7072->228.6,95.7072"),
    ("258da85d-f485-4412-95a9-5e0b6873ad91", "wire 259.08,95.7072->254,95.7072"),
    ("2d15a8bb-5599-4fa2-8628-62b2d26c3f25", "wire 228.6,80.4672->228.6,83.0072"),
    ("3354a6af-0ff4-4c79-a393-9f3312549ce3", "wire 228.6,90.6272->226.06,90.6272"),
    ("3b37d672-b030-41c7-a55c-66a70c82753f", "wire 254,95.7072->241.3,95.7072"),
    ("1f23067a-81ec-4c17-8df1-77b3215e7370", "wire 81.28,55.0672->93.98,55.0672"),
    ("9cc429e9-6101-4451-bcc1-d9e034f755bc", "wire 254,80.4672->259.08,80.4672"),
    ("9d8143e5-9e7e-4a78-9dba-de3c39c78e0b", "wire 254,88.0872->241.3,88.0872"),
    ("aebf2ef6-5256-48d7-b9f6-c696477627ab", "wire 254,93.1672->228.6,93.1672"),
    ("b41aa038-0bf0-4592-b4d7-b8a818524d4f", "wire 241.3,88.0872->241.3,95.7072"),
    ("cd5cfe97-926f-4be4-a09e-033a1287e77f", "wire 259.08,105.8672->259.08,95.7072"),
    ("e37bcf5e-c297-42f7-b173-d3c6b93abd76", "wire 68.58,55.0672->68.58,52.5272"),
    ("e91127cb-149d-4176-b174-37da621ca650", "wire 254,90.6272->254,93.1672"),
    ("eb30e5ab-92ce-4503-b54f-d3387eaf16dc", "wire 228.6,85.5472->254,85.5472"),
    ("ed20a903-5c95-43b5-b225-29d194c7e441", "wire 228.6,83.0072->254,83.0072"),
    ("5d790d5e-9629-4788-a6a6-51e2f6ee71ac", "wire 68.58,57.6072->81.28,57.6072"),
    ("67303a0a-b500-43bd-a97a-e078029962c2", "wire 228.6,75.3872->228.6,80.4672"),
    ("78a814d4-e535-467b-9584-252597a0ef76", "wire 55.88,57.6072->68.58,57.6072"),
    ("8ab35fe8-6fcc-4e3f-958c-06bf101a7967", "wire 81.28,57.6072->81.28,55.0672"),
    ("90c1f4eb-7e98-4f6e-ac96-fbc50d3a34b5", "wire 55.88,70.3072->55.88,57.6072"),
    ("5c637047-2969-4b17-8e2f-f2f083d4efb6", "wire 68.58,60.1472->78.74,60.1472"),
    ("560a499f-4476-4c33-9ff7-a4ed6fe29d29", "wire 50.8,52.5272->50.8,88.0872"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Modify wires
# ══════════════════════════════════════════════════════════════════════════════

old = '\t\t\t(xy 78.74 60.1472) (xy 78.74 47.4472)'
new = '\t\t\t(xy 78.74 57.6072) (xy 78.74 47.4472)'
if old in c:
    c = c.replace(old, new, 1); print("✓ wire modified: GP1 loop shortened")
else:
    errors.append("GP1 loop wire not found")

old2 = '\t\t\t(xy 226.06 90.6272) (xy 226.06 103.3272)'
new2 = '\t\t\t(xy 226.06 80.4672) (xy 226.06 103.3272)'
if old2 in c:
    c = c.replace(old2, new2, 1); print("✓ wire modified: output path y1 90.6272→80.4672")
else:
    errors.append("Output path wire not found")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: Insert new wires and junctions
# ══════════════════════════════════════════════════════════════════════════════

new_elements = '\n'.join([
    # IC1 area
    wire(76.2, 55.0672, 76.2, 47.4472),
    wire(76.2, 47.4472, 78.74, 47.4472),
    wire(86.36, 62.6872, 68.58, 62.6872),
    # IC? area
    wire(238.76, 85.5472, 238.76, 88.0872),
    wire(238.76, 88.0872, 228.6, 88.0872),
    wire(238.76, 75.3872, 251.46, 75.3872),
    wire(251.46, 75.3872, 251.46, 80.4672),
    wire(241.3, 80.4672, 226.06, 80.4672),
    wire(241.3, 90.6272, 259.08, 90.6272),
    wire(259.08, 90.6272, 259.08, 105.8672),
    # Junctions
    junction(76.2, 47.4472),
    junction(78.74, 47.4472),
    junction(251.46, 90.6272),
])

anchor = '\t(label "Voltage_IN"'
if anchor in c:
    c = c.replace(anchor, new_elements + '\n' + anchor, 1)
    print("✓ inserted 10 new wires + 3 junctions")
else:
    errors.append("Anchor 'Voltage_IN' label not found")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: Remove old +5V_BAR at 55.88,70.3072 and GND at 50.8,88.0872
# ══════════════════════════════════════════════════════════════════════════════

c = remove_by_uuid(c, "0644691d-5014-46c8-96f0-27be843ac528", "+5V_BAR at 55.88,70.3072")
c = remove_by_uuid(c, "ef01cdd0-4b57-4704-943f-4b304591d6d3", "GND at 50.8,88.0872")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7: Remove IC1 and IC? ALD1105 instances
# ══════════════════════════════════════════════════════════════════════════════

c = remove_by_uuid(c, "c3027455-e8fe-41bb-91b8-ad37d45da18a", "IC1 ALD1105")
c = remove_by_uuid(c, "655cdf0f-7f1f-4d28-aba4-da3ce63f718d", "IC? ALD1105")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 8: Add new MOSFET instances and power symbols
# ══════════════════════════════════════════════════════════════════════════════

# Same positions as BJT equivalents (pin positions are identical)
q3   = mosfet("Device:Q_NMOS",                       73.66,  49.9872,  0,   "Q3", "DMN2041UVT-7", ["G","D","S"])
q5   = mosfet("Device:Q_PMOS",                       83.82,  57.6072,  0,   "Q5", "DMP2110UVTQ-7", ["G","D","S"])
q7   = mosfet("neuromorphic:Q_NMOS_CurrentMirror",  233.68,  80.4672,  0,   "Q7", "DMN2041UVT-7", ["D1","D2","S1","S2"])
q8   = mosfet("neuromorphic:Q_PMOS_CurrentMirror",  246.38,  85.5472, 180,  "Q8", "DMP2110UVTQ-7", ["D1","D2","S1","S2"])
gnd3 = gnd_sym(76.2, 44.9072)
vcc5 = vcc_sym(86.36, 52.5272, rot=180)

new_syms = '\n'.join([q3, q5, q7, q8, gnd3, vcc5])

if c.rstrip().endswith(')'):
    last_nl = c.rfind('\n)')
    c = c[:last_nl] + '\n' + new_syms + '\n)'
    if c[-1] != '\n': c += '\n'
    print("✓ added Q3/Q5/Q7/Q8 MOSFETs + GND/+5V symbols")
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
print(f"\n✓ Delta.kicad_sch written ({len(c)} chars, {opens} parens)")
