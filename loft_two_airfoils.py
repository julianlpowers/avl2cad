import cadquery as cq
import numpy as np

# -----------------------------
# CONFIG
# -----------------------------

AF1 = "ag42d.dat"   # root
AF2 = "ag40d.dat"    # tip

ROOT_CHORD = 1.0
TIP_CHORD  = 0.7
SPAN       = 10.0

OUT_STEP = "airfoil_loft.step"


# -----------------------------
# AIRFOIL I/O
# -----------------------------

def load_airfoil(path):
    pts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                x, z = map(float, line.split()[:2])
                pts.append((x, z))
            except ValueError:
                continue
    return pts


def resample_to_reference(ref, pts):
    """Resample pts to match ref parameterization."""
    ref_n = len(ref)
    t_ref = np.linspace(0, 1, ref_n)
    t = np.linspace(0, 1, len(pts))

    pts = np.array(pts)
    x = np.interp(t_ref, t, pts[:, 0])
    z = np.interp(t_ref, t, pts[:, 1])

    return list(zip(x, z))


# -----------------------------
# CADQUERY HELPERS
# -----------------------------

def make_airfoil_wire(wp, pts, chord):
    """
    Create a closed wire on the current workplane.
    """
    scaled = [(x * chord, z * chord) for x, z in pts]
    return wp.polyline(scaled).close()


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    af1 = load_airfoil(AF1)
    af2 = load_airfoil(AF2)

    if len(af1) < 10 or len(af2) < 10:
        raise RuntimeError("Invalid airfoil data")

    # Preserve LE clustering
    af2 = resample_to_reference(af1, af2)

    # ---- Build loft properly ----
    wp = cq.Workplane("YZ")

    wp = make_airfoil_wire(wp, af1, ROOT_CHORD)
    wp = wp.workplane(offset=SPAN)
    wp = make_airfoil_wire(wp, af2, TIP_CHORD)

    solid = wp.loft(combine=True)

    cq.exporters.export(solid, OUT_STEP)
    print(f"Wrote {OUT_STEP}")
