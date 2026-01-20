import math

# --------------------------------------------------
# Geometry (2D X–Z)
# --------------------------------------------------

def rot_xz(p, a):
    """Rotate a 2D point in the XZ plane.
    
    Args:
        p: Tuple of (x, z) coordinates
        a: Rotation angle in radians
        
    Returns:
        Rotated (x, z) coordinates
    """
    ca, sa = math.cos(a), math.sin(a)
    x, z = p
    return (ca * x + sa * z, -sa * x + ca * z)


def rot_about_te(p, a, chord):
    """Rotate a point about the trailing edge.
    
    Args:
        p: Tuple of (x, z) coordinates
        a: Rotation angle in radians
        chord: Chord length
        
    Returns:
        Rotated (x, z) coordinates
    """
    x, z = p
    x -= chord
    x, z = rot_xz((x, z), a)
    return (x + chord, z)
