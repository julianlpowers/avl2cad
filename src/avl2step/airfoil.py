import numpy as np

# --------------------------------------------------
# Airfoil utilities
# --------------------------------------------------

def load_airfoil(path):
    """Load airfoil coordinates from a file.
    
    Args:
        path: Path to airfoil data file
        
    Returns:
        List of (x, z) coordinate tuples
    """
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
    """Resample airfoil points to match the number of points in a reference airfoil.
    
    Args:
        ref: Reference airfoil point list
        pts: Points to resample
        
    Returns:
        Resampled point list with same length as ref
    """
    t_ref = np.linspace(0, 1, len(ref))
    t = np.linspace(0, 1, len(pts))
    pts = np.array(pts)
    x = np.interp(t_ref, t, pts[:, 0])
    z = np.interp(t_ref, t, pts[:, 1])
    return list(zip(x, z))


def flat_plate(n=120):
    """Generate a flat plate airfoil.
    
    Args:
        n: Total number of points
        
    Returns:
        List of (x, z) coordinates forming a flat plate
    """
    x = np.linspace(1, 0, n // 2)
    return list(zip(x, np.zeros_like(x))) + list(zip(x[::-1], np.zeros_like(x)))
