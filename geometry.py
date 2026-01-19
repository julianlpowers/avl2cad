import math

# --------------------------------------------------
# Geometry (2D X–Z)
# --------------------------------------------------

def rot_xz(p, a):
    ca, sa = math.cos(a), math.sin(a)
    x, z = p
    return (ca * x + sa * z, -sa * x + ca * z)


def rot_about_te(p, a, chord):
    x, z = p
    x -= chord
    x, z = rot_xz((x, z), a)
    return (x + chord, z)