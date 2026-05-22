#!/usr/bin/env python3
"""Fix C/E pin swap on Q3 (NPN) and Q5 (PNP) in Delta.kicad_sch.

Actual pin positions for Device:Q_NPN and Device:Q_PNP at 0-degree rotation:
  C at local (2.54, +5.08) -> sch_y = cy - 5.08  (UPPER / smaller y)
  E at local (2.54, -5.08) -> sch_y = cy + 5.08  (LOWER / larger y)

Q3 at (73.66, 49.9872): C=(76.2, 44.9072), E=(76.2, 55.0672)
Q5 at (83.82, 57.6072): C=(86.36, 52.5272), E=(86.36, 62.6872)

Bug: GND was placed at Q3-C, node_A wire went to Q3-E.
     +5V was placed at Q5-C, output wire went to Q5-E.
Fix: swap so GND->E, C->node_A; +5V->E, C->output.
"""
import re, uuid

SCH = "/home/todd/Documents/Thesis/neuromorphic circuit/neurosynaptic/PCBdesign/kicad/Synapse/Delta.kicad_sch"

with open(SCH) as f:
    text = f.read()

errors = []

def new_uuid():
    return str(uuid.uuid4())

def remove_by_uuid(t, uid, label=""):
    idx = t.find('"' + uid + '"')
    if idx < 0:
        errors.append(f"UUID not found: {uid} ({label})")
        return t
    block_start = t.rfind('\n\t(', 0, idx)
    if block_start < 0:
        errors.append(f"Block start not found for {uid} ({label})")
        return t
    depth = 0; i = block_start + 1; end = -1
    while i < len(t):
        if t[i] == '(':
            depth += 1
        elif t[i] == ')':
            depth -= 1
            if depth == 0:
                end = i
                break
        i += 1
    if end < 0:
        errors.append(f"Block end not found for {uid} ({label})")
        return t
    return t[:block_start] + t[end+1:]

def wire(x1, y1, x2, y2):
    u = new_uuid()
    return f"""
\t(wire
\t\t(pts
\t\t\t(xy {x1} {y1}) (xy {x2} {y2})
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{u}")
\t)"""

def gnd_sym(x, y):
    u1, u2 = new_uuid(), new_uuid()
    return f"""
\t(symbol
\t\t(lib_id "Synapse_LPS-altium-import:GND_POWER_GROUND")
\t\t(at {x} {y} 0)
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "{u1}")
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
\t\t(property "Value" "GND"
\t\t\t(at {x} {round(y + 6.35, 4)} 0)
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
\t\t\t(uuid "{u2}")
\t\t)
\t\t(instances
\t\t\t(project "Synapse_LPS"
\t\t\t\t(path "/af4a7426-c915-4fd8-a9a0-d1d0653890c7/984ef279-a542-4986-b306-8a6747a54659"
\t\t\t\t\t(reference "#PWR?")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""

def vcc_sym(x, y, rot=0):
    u1, u2 = new_uuid(), new_uuid()
    # Value text offset: for 0-deg, bar graphic is above pin so text is above
    text_y = round(y - 3.81, 4)
    return f"""
\t(symbol
\t\t(lib_id "Synapse_LPS-altium-import:+5V_BAR")
\t\t(at {x} {y} {rot})
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "{u1}")
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
\t\t(property "Value" "+5V"
\t\t\t(at {x} {text_y} 0)
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
\t\t\t(uuid "{u2}")
\t\t)
\t\t(instances
\t\t\t(project "Synapse_LPS"
\t\t\t\t(path "/af4a7426-c915-4fd8-a9a0-d1d0653890c7/984ef279-a542-4986-b306-8a6747a54659"
\t\t\t\t\t(reference "#PWR?")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""

# ──────────────────────────────────────────────
# STEP 1: Remove wrong elements
# ──────────────────────────────────────────────

# Q3: GND wrongly at C=(76.2, 44.9072)
text = remove_by_uuid(text, "9b072c8e-e669-4c9d-b28e-28bd626a0c7d", "GND@Q3-C(wrong)")

# Q3: wire E=(76.2,55.0672)->node_A=(76.2,47.4472) [wrong: emitter to node_A]
text = remove_by_uuid(text, "10e013af-64c0-4568-ae95-7eaee3c2953d", "wire Q3-E->node_A(wrong)")

# Q5: +5V wrongly at C=(86.36, 52.5272)
text = remove_by_uuid(text, "cf282a26-44ac-4179-8c4c-674f84f805b9", "+5V@Q5-C(wrong)")

# Q5: wire E=(86.36,62.6872)->DEL=(68.58,62.6872) [wrong: emitter to output]
text = remove_by_uuid(text, "9c2cf546-a799-4aee-8e38-cb582f308de4", "wire Q5-E->DEL(wrong)")

# ──────────────────────────────────────────────
# STEP 2: Add correct elements before final closing paren
# ──────────────────────────────────────────────
additions = ""

# Q3 fix: GND at E=(76.2, 55.0672)
additions += gnd_sym(76.2, 55.0672)

# Q3 fix: wire C=(76.2,44.9072) -> node_A=(76.2,47.4472)
additions += wire(76.2, 44.9072, 76.2, 47.4472)

# Q5 fix: +5V at E=(86.36, 62.6872)  [0-deg: bar graphic above pin]
additions += vcc_sym(86.36, 62.6872, rot=0)

# Q5 fix: C=(86.36,52.5272) -> route left then down to DEL=(68.58,62.6872)
additions += wire(86.36, 52.5272, 68.58, 52.5272)   # C -> left
additions += wire(68.58, 52.5272, 68.58, 62.6872)    # down to DEL

# Insert before final \n)
assert text.endswith('\n)\n') or text.endswith('\n)'), f"unexpected file ending: {repr(text[-10:])}"
if text.endswith('\n)\n'):
    text = text[:-3] + additions + '\n)\n'
else:
    text = text[:-2] + additions + '\n)\n'

if errors:
    print("ERRORS:")
    for e in errors:
        print(" ", e)
else:
    with open(SCH, 'w') as f:
        f.write(text)
    print("Done. No errors.")
    # Verify paren balance
    opens = text.count('(')
    closes = text.count(')')
    print(f"Paren balance: {opens} open, {closes} close, delta={opens-closes}")
