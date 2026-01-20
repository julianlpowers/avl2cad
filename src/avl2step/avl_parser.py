# --------------------------------------------------
# AVL parsing helpers
# --------------------------------------------------

def skip_comments(lines, i):
    """Skip comment lines starting with # or !.
    
    Args:
        lines: List of all lines
        i: Current line index
        
    Returns:
        Index of next non-comment line
    """
    while i < len(lines) and (lines[i].startswith('#') or lines[i].startswith('!')):
        i += 1
    return i


def read_values(line, lines, i, n):
    """Read numeric values from AVL file lines.
    
    Args:
        line: Current line
        lines: All lines in the file
        i: Current line index
        n: Number of values to read
        
    Returns:
        Tuple of (values list, new line index)
    """
    parts = line.split()
    if len(parts) >= n + 1:
        return list(map(float, parts[1:1+n])), i
    else:
        # Skip comment lines when reading next line
        next_i = skip_comments(lines, i + 1)
        return list(map(float, lines[next_i].split()[:n])), next_i


def parse_avl(filename):
    """Parse an AVL aircraft geometry file.
    
    Args:
        filename: Path to AVL file
        
    Returns:
        List of surface dictionaries containing geometry data
    """
    surfaces = []
    current = None

    with open(filename, encoding="latin-1") as f:
        lines = [l.strip() for l in f.readlines()]

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip comment lines (start with # or !)
        if line.startswith('#') or line.startswith('!'):
            i += 1
            continue

        if line == "SURFACE":
            # Skip comments to find surface name
            name_i = skip_comments(lines, i + 1)
            current = {
                "name": lines[name_i],
                "angle": 0.0,
                "scale": (1.0, 1.0, 1.0),
                "translate": (0.0, 0.0, 0.0),
                "ydup": None,
                "sections": []
            }
            surfaces.append(current)
            i = name_i + 1
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
                # Skip comments to find section data
                data_i = skip_comments(lines, i + 1)
                vals = lines[data_i].split()
                current["sections"].append({
                    "x": float(vals[0]),
                    "y": float(vals[1]),
                    "z": float(vals[2]),
                    "c": float(vals[3]),
                    "ainc": float(vals[4]) if len(vals) > 4 else 0.0,
                    "airfoil": None
                })
                i = data_i

            elif line.startswith("AFIL"):
                # Skip comments to find airfoil filename
                afil_i = skip_comments(lines, i + 1)
                current["sections"][-1]["airfoil"] = lines[afil_i].strip()
                i = afil_i

        i += 1

    return surfaces
