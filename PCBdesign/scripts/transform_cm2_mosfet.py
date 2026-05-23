#!/usr/bin/env python3
"""Transform Current Mirror_2.kicad_sch: replace ALD1105PBL with discrete MOSFET equivalents.

ALD (*:2_0_ALD1105PBL_*) → Q_NMOS_CurrentMirror + Q_PMOS_CurrentMirror (neuromorphic lib)
Pin positions identical to BJT equivalents; all wires reused unchanged.
"""

import uuid, re, sys

BASE      = "/home/todd/Documents/Thesis/neuromorphic circuit/neurosynaptic/PCBdesign"
SCH       = f'{BASE}/kicad/Synapse/Current Mirror_2.kicad_sch'
NEURO     = f"{BASE}/kicad/lib/neuromorphic.kicad_sym"
PROJ      = "/af4a7426-c915-4fd8-a9a0-d1d0653890c7/c9470723-b410-4315-971f-b3c2471482a7"
PROJ_NAME = "Synapse_LPS"

def gu(): return str(uuid.uuid4())

with open(SCH)   as f: c     = f.read()
with open(NEURO) as f: neuro = f.read()

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

ald_match = re.search(r'\t\t\(symbol "\*:2_0_ALD1105PBL_\*".*?\(embedded_fonts no\)\n\t\t\)',
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

c = remove_by_uuid(c, "6a798f2f-0008-41dc-ab62-e0630a07c05f", "IC1 ALD1105PBL *:2_0*")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: Remove junctions
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("03cec0ff-1890-4e5d-9118-368930c1b5b2", "junction (113.03,99.5172)"),
    ("289f984a-1fb6-4bc7-8a23-bd8662bc17f6", "junction (124.46,91.8972)"),
    ("729923ce-0241-43a5-aea1-fc8f11a6b985", "junction (124.46,94.4372)"),
    ("a24b243c-4ef9-4f75-94c5-d7f621c64194", "junction (154.94,104.5972)"),
    ("ca15c0ac-47ea-484a-93b1-903dd4eaf12c", "junction (160.02,91.8972)"),
    ("e59b50b1-a94d-428b-9a8c-ea05d3aa3011", "junction (124.46,96.9772)"),
    ("e5b473da-523d-423b-8336-f2066fbe86fa", "junction (149.86,107.1372)"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: Remove wires
# ══════════════════════════════════════════════════════════════════════════════

for uid, desc in [
    ("0154b6d2-a48c-4200-a18f-e0da9d0f533b", "wire 116.84,119.8372->167.64,119.8372"),
    ("02e09b13-c04c-403b-9a77-b0b0c544266d", "wire 154.94,102.0572->154.94,104.5972"),
    ("0b6e3bd3-2026-4e4a-b32b-8172b8557dea", "wire 124.46,90.6272->124.46,91.8972"),
    ("14263d68-3219-4eec-bc3e-953f92f24189", "wire 149.86,102.0572->154.94,102.0572"),
    ("149cc011-5d09-4deb-8ce3-9641f2d9bbff", "wire 149.86,96.9772->124.46,96.9772"),
    ("166fd6f4-860c-4f3e-ab42-75cb783828f0", "wire 113.03,96.9772->113.03,99.5172"),
    ("1f16375d-6299-4b0f-a838-6c8ad3f793b1", "wire 120.65,104.5972->124.46,104.5972"),
    ("21e495a1-00a9-44e0-8b93-299658341476", "wire 139.7,107.1372->149.86,107.1372"),
    ("33e8c041-b890-4e32-ba15-89a18ee83f9e", "wire 149.86,113.4872->124.46,113.4872"),
    ("370c1086-98ab-4e59-b7d3-f73a4614fb8d", "wire 149.86,91.8972->160.02,91.8972"),
    ("3cc9a8dc-bc2d-489e-8264-aef952c77088", "wire 124.46,113.4872->124.46,107.1372"),
    ("5e88aedd-4ff3-4aa0-ba60-6b8397e3887f", "wire 113.03,99.5172->113.03,126.1872"),
    ("68db0e67-cf65-46cc-8e49-215b9b681101", "wire 149.86,104.5972->154.94,104.5972"),
    ("6a35253a-e2de-4874-8ad5-5c97174c3d09", "wire 116.84,102.0572->116.84,119.8372"),
    ("7737c96d-0be3-4fdd-af33-156b9335a195", "wire 144.78,99.5172->139.7,99.5172"),
    ("796f4444-d22e-4c43-9613-05f05b5388e2", "wire 120.65,116.0272->120.65,104.5972"),
    ("7e09ac32-b1b2-46a6-beaf-e60dc33287a8", "wire 160.02,91.8972->167.64,91.8972"),
    ("888845ca-c3c8-4f6d-bba0-9d828d5242bd", "wire 154.94,99.5172->149.86,99.5172"),
    ("99014f7d-48d9-4e54-8cbb-d00b676e10b8", "wire 139.7,99.5172->139.7,107.1372"),
    ("a04007fd-dd3f-4497-89ed-1cae1a75d153", "wire 109.22,90.6272->124.46,90.6272"),
    ("aae7449b-2be5-4121-be0c-c7a0d0f53382", "wire 124.46,91.8972->124.46,94.4372"),
    ("ad61118e-acea-4abe-aa67-e6cc8a13b259", "wire 124.46,96.9772->113.03,96.9772"),
    ("b989c2b6-9316-4006-ae27-354acadcfb6f", "wire 124.46,102.0572->116.84,102.0572"),
    ("c8a90298-f732-4c49-889f-7d64cc38168a", "wire 124.46,99.5172->113.03,99.5172"),
    ("d27807e3-d9de-46bc-ab16-43f4614ae8de", "wire 149.86,107.1372->149.86,113.4872"),
    ("d5ee7c33-a49b-4450-8c51-1ef47b9652b4", "wire 154.94,104.5972->160.02,104.5972"),
    ("daab1ebe-8a7d-4bfb-81fa-8884d02ba7fb", "wire 154.94,104.5972->154.94,116.0272"),
    ("defdd00a-e8b4-402f-afce-034f39c7c9ec", "wire 154.94,116.0272->120.65,116.0272"),
    ("ff9fa59a-5a46-4dad-9ffc-b57ca8b86370", "wire 124.46,94.4372->149.86,94.4372"),
]:
    c = remove_by_uuid(c, uid, desc)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5: Remove old power symbols
# ══════════════════════════════════════════════════════════════════════════════

c = remove_by_uuid(c, "2e4d83c3-ae28-4abf-99e6-9fceb8486ec4", "+5V_BAR at (154.94,99.5172)")
c = remove_by_uuid(c, "908e3d23-e969-4151-a59a-cb0bd15b1946", "GND at (113.03,126.1872)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6: Insert new wires, junction, power symbols, and MOSFET instances
# ══════════════════════════════════════════════════════════════════════════════

q_nmos = mosfet("neuromorphic:Q_NMOS_CurrentMirror", 125.73, 109.6772, 0, "Q5", "DMN2041UVT-7",  ["D1","D2","S1","S2"])
q_pmos = mosfet("neuromorphic:Q_PMOS_CurrentMirror", 125.73,  94.4372, 0, "Q6", "DMP2110UVTQ-7", ["S1","S2","D1","D2"])

vcc1 = vcc_sym(120.65, 89.3572)
vcc2 = vcc_sym(130.81, 89.3572)
gnd1 = gnd_sym(120.65, 114.7572)
gnd2 = gnd_sym(130.81, 114.7572)

new_elements = '\n'.join([
    wire(109.22,  90.6272, 120.65,  90.6272),
    wire(120.65,  90.6272, 120.65,  99.5172),
    wire(120.65,  99.5172, 120.65, 104.5972),
    wire(130.81, 104.5972, 160.02, 104.5972),
    wire(160.02,  91.8972, 167.64,  91.8972),
    wire(130.81,  99.5172, 155.0,   99.5172),
    wire(155.0,   99.5172, 155.0,  119.8372),
    wire(155.0,  119.8372, 167.64, 119.8372),
    junction(120.65, 99.5172),
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
    print("✓ added Q5/Q6 MOSFET instances + 4 power symbols")
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
print(f"\n✓ Current Mirror_2.kicad_sch written ({len(c)} chars, {opens} parens)")
