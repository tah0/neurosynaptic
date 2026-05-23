#!/usr/bin/env python3
"""
Annotate KiCad schematics — fix duplicate refs, ? refs, and * suffix refs.

Synapse_LPS sub-sheets (Delta, CM1, CM2) share ref namespace.
Current_Source is a separate project with its own namespace.
"""

import re, sys

BASE = "/home/todd/Documents/Thesis/neuromorphic circuit/neurosynaptic/PCBdesign/kicad"

SYNAPSE_FILES = [
    ("Root",    f"{BASE}/Synapse/Synapse_LPS.kicad_sch"),
    ("Delta",   f"{BASE}/Synapse/Delta.kicad_sch"),
    ("CM1",     f"{BASE}/Synapse/Current Mirror_1.kicad_sch"),
    ("CM2",     f"{BASE}/Synapse/Current Mirror_2.kicad_sch"),
]
CS_FILES = [
    ("CurrentSource", f"{BASE}/CurrentSource/Current_Source.kicad_sch"),
]

# ── helpers ───────────────────────────────────────────────────────────────────

def read(path):
    with open(path) as f: return f.read()

def write(path, txt):
    with open(path, 'w') as f: f.write(txt)

def instance_start(txt):
    """Return offset where symbol instances begin (after lib_symbols block)."""
    for marker in ['\n\t)\n\t(symbol\n', '\n\t)\n\t(junction', '\n\t)\n\t(wire']:
        i = txt.find(marker)
        if i >= 0: return i
    return 0

def get_refs(txt):
    """Return list of (ref, span_start, span_end) for all non-power property refs in instances."""
    start = instance_start(txt)
    results = []
    for m in re.finditer(r'\(property "Reference" "([^"]+)"', txt[start:]):
        ref = m.group(1)
        if ref.startswith('#'): continue
        abs_start = start + m.start()
        abs_end   = start + m.end()
        results.append((ref, abs_start, abs_end))
    return results

def get_instance_refs(txt):
    """Return list of (ref, span_start, span_end) inside (instances ... (reference "Xn")) blocks."""
    results = []
    for m in re.finditer(r'\(reference "([^"]+)"\)', txt):
        ref = m.group(1)
        if ref.startswith('#'): continue
        results.append((ref, m.start(), m.end()))
    return results

def replace_ref(txt, old_ref, new_ref, limit=1):
    """Replace first `limit` occurrences of (property "Reference" "old") and (reference "old")."""
    prop_pat  = f'(property "Reference" "{re.escape(old_ref)}"'
    inst_pat  = f'(reference "{re.escape(old_ref)}")'
    count = [0]
    def repl_prop(m):
        if count[0] < limit:
            count[0] += 1
            return f'(property "Reference" "{new_ref}"'
        return m.group(0)
    txt = re.sub(re.escape(prop_pat), repl_prop, txt)
    count[0] = 0
    def repl_inst(m):
        if count[0] < limit:
            count[0] += 1
            return f'(reference "{new_ref}")'
        return m.group(0)
    txt = re.sub(re.escape(inst_pat), repl_inst, txt)
    return txt

def replace_all_ref(txt, old_ref, new_ref):
    txt = txt.replace(f'(property "Reference" "{old_ref}"', f'(property "Reference" "{new_ref}"')
    txt = txt.replace(f'(reference "{old_ref}")',            f'(reference "{new_ref}")')
    return txt

def prefix(ref):
    """Extract letter prefix from ref: 'RD1*' → 'RD', 'Q3' → 'Q', 'J?' → 'J'."""
    m = re.match(r'^([A-Za-z]+)', ref)
    return m.group(1) if m else ref

def next_num(used_nums):
    n = 1
    while n in used_nums: n += 1
    return n

# ── collect current state ─────────────────────────────────────────────────────

def collect(file_list):
    data = {}
    for name, path in file_list:
        txt = read(path)
        start = instance_start(txt)
        refs = re.findall(r'\(property "Reference" "([^"]+)"', txt[start:])
        refs = [r for r in refs if not r.startswith('#')]
        data[name] = {'path': path, 'txt': txt, 'refs': refs}
    return data

# ── annotate a namespace (list of sheets sharing refs) ────────────────────────

def annotate_namespace(data, file_list):
    # Build map: prefix → set of current numeric suffixes (clean ints)
    used = {}  # prefix → set of int
    for name, _ in file_list:
        for ref in data[name]['refs']:
            p = prefix(ref)
            m = re.search(r'(\d+)', ref)
            if m and '?' not in ref and '*' not in ref:
                used.setdefault(p, set()).add(int(m.group(1)))
            else:
                used.setdefault(p, set())

    changes = []  # (sheet_name, old_ref, new_ref)

    # Pass 1: strip * suffix (RD1* → RD1, RC1* → RC1, Ral* → Ral1, Rex* → Rex1)
    for name, _ in file_list:
        new_refs = []
        for ref in data[name]['refs']:
            if '*' in ref and '?' not in ref:
                p = prefix(ref)
                m = re.search(r'(\d+)', ref)
                if m:
                    new_ref = p + m.group(1)
                    used.setdefault(p, set()).add(int(m.group(1)))
                else:
                    # No digit (e.g. Ral*, Rex*) — assign next number
                    n = next_num(used.get(p, set()))
                    used.setdefault(p, set()).add(n)
                    new_ref = p + str(n)
                changes.append((name, ref, new_ref))
                new_refs.append(new_ref)
            else:
                new_refs.append(ref)
        data[name]['refs'] = new_refs

    # Pass 2: fix ? refs
    for name, _ in file_list:
        new_refs = []
        for ref in data[name]['refs']:
            if '?' in ref:
                p = prefix(ref)
                n = next_num(used.get(p, set()))
                used.setdefault(p, set()).add(n)
                new_ref = p + str(n)
                changes.append((name, ref, new_ref))
                new_refs.append(new_ref)
            else:
                new_refs.append(ref)
        data[name]['refs'] = new_refs

    # Pass 3: fix duplicates across sheets
    seen = {}  # ref → first sheet name
    for name, _ in file_list:
        new_refs = []
        for ref in data[name]['refs']:
            if ref in seen and seen[ref] != name:
                # conflict — assign new number
                p = prefix(ref)
                n = next_num(used.get(p, set()))
                used.setdefault(p, set()).add(n)
                new_ref = p + str(n)
                changes.append((name, ref, new_ref))
                seen[new_ref] = name
                new_refs.append(new_ref)
            else:
                seen[ref] = name
                new_refs.append(ref)
        data[name]['refs'] = new_refs

    return changes

# ── apply changes to file text ────────────────────────────────────────────────

def apply_changes(data, changes, file_list):
    for name, path in file_list:
        sheet_changes = [(o, n) for (s, o, n) in changes if s == name]
        if not sheet_changes:
            continue
        txt = data[name]['txt']
        # Count how many times each old_ref appears in the change list for this sheet.
        # If a ref appears multiple times (e.g. two J? → J1, J2), replace one instance
        # at a time to avoid clobbering the second occurrence.
        from collections import Counter
        old_counts = Counter(o for o, n in sheet_changes)
        if all(v == 1 for v in old_counts.values()):
            # Simple case — no duplicate old refs, replace all
            for old, new in sheet_changes:
                txt = replace_all_ref(txt, old, new)
                print(f"  [{name}] {old} → {new}")
        else:
            # One or more old refs appear multiple times — replace one occurrence at a time
            # using a temp sentinel to avoid cascading replacements
            import uuid
            sentinels = {}
            # First pass: replace each occurrence with a unique sentinel
            for old, new in sheet_changes:
                sentinel = f"__ANNOT_{uuid.uuid4().hex[:8]}__"
                sentinels[sentinel] = new
                # Replace only the first remaining occurrence of old
                prop_old = f'(property "Reference" "{old}"'
                prop_new = f'(property "Reference" "{sentinel}"'
                inst_old = f'(reference "{old}")'
                inst_new = f'(reference "{sentinel}")'
                txt = txt.replace(prop_old, prop_new, 1)
                txt = txt.replace(inst_old, inst_new, 1)
                print(f"  [{name}] {old} → {new}")
            # Second pass: replace sentinels with final refs
            for sentinel, new in sentinels.items():
                txt = txt.replace(f'(property "Reference" "{sentinel}"',
                                  f'(property "Reference" "{new}"')
                txt = txt.replace(f'(reference "{sentinel}")',
                                  f'(reference "{new}")')
        data[name]['txt'] = txt

# ── main ──────────────────────────────────────────────────────────────────────

print("=== Synapse LPS ===")
syn_data = collect(SYNAPSE_FILES)
syn_changes = annotate_namespace(syn_data, SYNAPSE_FILES)
apply_changes(syn_data, syn_changes, SYNAPSE_FILES)

print("\n=== Current Source ===")
cs_data = collect(CS_FILES)
cs_changes = annotate_namespace(cs_data, CS_FILES)
apply_changes(cs_data, cs_changes, CS_FILES)

# Write all modified files
all_data = {**syn_data, **cs_data}
all_files = SYNAPSE_FILES + CS_FILES
for name, path in all_files:
    write(path, all_data[name]['txt'])
    print(f"\n✓ written: {name}")

print("\nDone. Re-run netlist export to verify.")
