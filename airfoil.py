import numpy as np

# --------------------------------------------------
# Airfoil utilities
# --------------------------------------------------

def load_airfoil(path):
    pts = []
    with open(path) as f:
        for l in f:
            try:
                x, z = map(float, l.split()[:2])
                pts.append((x, z))
            except:
                pass
    return pts


def resample_to_reference(ref, pts):
    t_ref = np.linspace(0, 1, len(ref))
    t = np.linspace(0, 1, len(pts))
    pts = np.array(pts)
    x = np.interp(t_ref, t, pts[:, 0])
    z = np.interp(t_ref, t, pts[:, 1])
    return list(zip(x, z))


def flat_plate(n=120):
    x = np.linspace(1, 0, n // 2)
    return list(zip(x, np.zeros_like(x))) + list(zip(x[::-1], np.zeros_like(x)))