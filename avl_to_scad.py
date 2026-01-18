import math

AVL_PATH = "/home/julianpo/supra.avl"
OUT_SCAD = "supra.scad"

THICKNESS = 0.02
RAD = math.pi / 180.0


# --------------------------------------------------
# AVL helper: read numeric blocks (1-line or 2-line)
# --------------------------------------------------

def read_values(line, lines, i, n):
    parts = line.split()
    if len(parts) >= n + 1:
        return list(map(float, parts[1:1+n])), i
    else:
        return list(map(float, lines[i+1].split()[:n])), i + 1


# --------------------------------------------------
# Parse AVL geometry
# --------------------------------------------------

def parse_avl(filename):
    surfaces = []
    current = None

    with open(filename, encoding="latin-1") as f:
        lines = [l.strip() for l in f.readlines()]

    i = 0
    while i < len(lines):
        line = lines[i]

        if line == "SURFACE":
            current = {
                "name": lines[i+1],
                "angle": 0.0,
                "scale": (1.0, 1.0, 1.0),
                "translate": (0.0, 0.0, 0.0),
                "ydup": None,
                "sections": []
            }
            surfaces.append(current)
            i += 2
            continue

        if current is not None:

            if line.startswith("ANGLE"):
                vals, i = read_values(line, lines, i, 1)
                current["angle"] = vals[0]

            elif line.startswith("SCALE"):
                vals, i = read_values(line, lines, i, 3)
                current["scale"] = tuple(vals)

            elif line.startswith("TRANSLATE"):
                vals, i = read_values(line, lines, i, 3)
                current["translate"] = tuple(vals)

            elif line.startswith("YDUPLICATE"):
                vals, i = read_values(line, lines, i, 1)
                current["ydup"] = vals[0]

            elif line == "SECTION":
                vals = lines[i+1].split()
                current["sections"].append({
                    "x": float(vals[0]),
                    "y": float(vals[1]),
                    "z": float(vals[2]),
                    "c": float(vals[3]),
                    "ainc": float(vals[4]) if len(vals) > 4 else 0.0
                })
                i += 1

        i += 1

    return surfaces


# --------------------------------------------------
# Geometry math
# --------------------------------------------------

def rot_y(p, a):
    ca, sa = math.cos(a), math.sin(a)
    return (ca*p[0] + sa*p[2], p[1], -sa*p[0] + ca*p[2])

def scale(p, s):
    return (p[0]*s[0], p[1]*s[1], p[2]*s[2])

def translate(p, t):
    return (p[0]+t[0], p[1]+t[1], p[2]+t[2])

def mirror_y_about(p, y0):
    return (p[0], 2*y0 - p[1], p[2])

def vec(p):
    return f"[{p[0]:.5f}, {p[1]:.5f}, {p[2]:.5f}]"

def rot_y_about_te(p, angle, te):
    """
    Rotate point p about a Y-axis passing through the trailing edge (x = chord).
    """
    # move TE to origin
    p0 = (p[0] - te[0], p[1] - te[1], p[2])
    # rotate
    p1 = rot_y(p0, angle)
    # move back
    return (p1[0] + te[0], p1[1] + te[1], p1[2])



# --------------------------------------------------
# Build section geometry (AVL-faithful)
# --------------------------------------------------

def build_section(section, surf):
    c = section["c"]
    ainc = section["ainc"] * RAD
    inc  = surf["angle"] * RAD
    
    # flat plate chord
    p1 = (0, 0, 0)
    p2 = (c, 0, 0)


    # 1) place at leading edge
    le = (section["x"], section["y"], section["z"])
    p1 = translate(p1, le)
    p2 = translate(p2, le)

    # 2) surface SCALE (dihedral lives here)
    p1 = scale(p1, surf["scale"])
    p2 = scale(p2, surf["scale"])

    # 3) surface TRANSLATE
    p1 = translate(p1, surf["translate"])
    p2 = translate(p2, surf["translate"])

    # 4) surface incidence (ANGLE + AINC) about TE
    p1 = rot_y_about_te(p1, ainc + inc, p2)
    
    return p1, p2


# --------------------------------------------------
# Generate OpenSCAD
# --------------------------------------------------

surfaces = parse_avl(AVL_PATH)

scad = []
scad.append(f"t = {THICKNESS};")
scad.append("union() {")

for surf in surfaces:
    print(f"\nBuilding SURFACE: {surf['name']}")
    print(f"  ANGLE     = {surf['angle']} deg")
    print(f"  SCALE     = {surf['scale']}")
    print(f"  TRANSLATE = {surf['translate']}")
    if surf["ydup"] is not None:
        print(f"  YDUPLICATE about Y = {surf['ydup']}")

    # ---- build all sections ----
    sections = []
    for s in surf["sections"]:
        p1, p2 = build_section(s, surf)
        sections.append((p1, p2))
        print(f"  SECTION @ ({s['x']},{s['y']},{s['z']})  ainc={s['ainc']}")

    # ---- build panel geometry ONCE ----
    surface_panels = []

    for i in range(len(sections) - 1):
        a1, a2 = sections[i]
        b1, b2 = sections[i + 1]

        surface_panels.append(f"""
        polyhedron(
          points=[
            {vec(a1)}, {vec(a2)}, {vec(b2)}, {vec(b1)},
            [{a1[0]}, {a1[1]}, {a1[2]}+t],
            [{a2[0]}, {a2[1]}, {a2[2]}+t],
            [{b2[0]}, {b2[1]}, {b2[2]}+t],
            [{b1[0]}, {b1[1]}, {b1[2]}+t]
          ],
          faces=[
            [0,1,2,3],[4,5,6,7],
            [0,1,5,4],[1,2,6,5],
            [2,3,7,6],[3,0,4,7]
          ]
        );
        """)

    scad.append(f"// Surface: {surf['name']}")
    scad.append("union() {")

    # ---- original surface ----
    for panel in surface_panels:
        scad.append(panel)

    # ---- mirrored surface (YDUPLICATE) ----
    if surf["ydup"] is not None:
        y0 = surf["ydup"]
        scad.append(f"""
        translate([0,{y0},0])
            mirror([0,1,0])
                translate([0,{-y0},0]) {{
        """)
        for panel in surface_panels:
            scad.append(panel)
        scad.append("}")

    scad.append("}")

scad.append("}")

with open(OUT_SCAD, "w") as f:
    f.write("\n".join(scad))

print("\nWrote supra.scad")

