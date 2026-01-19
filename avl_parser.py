


# --------------------------------------------------
# AVL parsing helpers
# --------------------------------------------------

def read_values(line, lines, i, n):
    parts = line.split()
    if len(parts) >= n + 1:
        return list(map(float, parts[1:1+n])), i
    else:
        return list(map(float, lines[i+1].split()[:n])), i + 1


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
                v, i = read_values(line, lines, i, 1)
                current["angle"] = v[0]

            elif line.startswith("SCALE"):
                v, i = read_values(line, lines, i, 3)
                current["scale"] = tuple(v)

            elif line.startswith("TRANSLATE"):
                v, i = read_values(line, lines, i, 3)
                current["translate"] = tuple(v)

            elif line.startswith("YDUPLICATE"):
                v, i = read_values(line, lines, i, 1)
                current["ydup"] = v[0]

            elif line == "SECTION":
                vals = lines[i+1].split()
                current["sections"].append({
                    "x": float(vals[0]),
                    "y": float(vals[1]),
                    "z": float(vals[2]),
                    "c": float(vals[3]),
                    "ainc": float(vals[4]) if len(vals) > 4 else 0.0,
                    "airfoil": None
                })
                i += 1

            elif line.startswith("AFIL"):
                current["sections"][-1]["airfoil"] = lines[i+1].strip()
                i += 1

        i += 1

    return surfaces