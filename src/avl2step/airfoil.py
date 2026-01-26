import numpy as np
from scipy.interpolate import splprep, splev

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



def densify_airfoil_points(pts, n_points=200, per=False):
    """
    Densify airfoil points using cubic spline interpolation.
    Args:
        pts: List of (x, y) tuples.
        n_points: Number of output points.
        per: If True, treat as periodic (closed curve).
    Returns:
        List of (x, y) tuples with increased density.
    """
    pts = np.array(pts)
    tck, u = splprep([pts[:,0], pts[:,1]], s=0, per=per)
    # Use a cosine spacing to cluster points near u=0.5
    theta = np.linspace(0, np.pi, n_points)
    u_new = 0.5 * (1 - np.cos(theta))
    x_new, y_new = splev(u_new, tck)
    return list(zip(x_new, y_new))






