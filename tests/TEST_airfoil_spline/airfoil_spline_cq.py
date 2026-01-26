import sys
from pathlib import Path
import cadquery as cq
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from avl2step.airfoil import load_airfoil
from avl2step.converter import split_airfoil_surfaces

def main():
    airfoil_file = "ag40d.dat"
    pts = load_airfoil(airfoil_file)
    # pts = split_airfoil_surfaces(pts)
    print(f"Loaded {len(pts)} points from {airfoil_file}")
    # CadQuery expects (x, y, z)
    # All points in XY plane, only scale x and z
    a1 = [(x*100, z*100, 0) for x, z in pts]
    a2 = [(x*50+25,  z*50,  0) for x, z in pts]
    a3 = [(x*10+25,  z*10,  0) for x, z in pts]

    # Loft using workplane offsets along Y
    wp = cq.Workplane("XY")
    wp = wp.splineApprox(a1, minDeg=3, includeCurrent=False).close().wire()
    wp = wp.workplane(offset=50).splineApprox(a2, minDeg=3, includeCurrent=False).close().wire()
    wp = wp.workplane(offset=20).splineApprox(a3, minDeg=3, includeCurrent=False).close().wire()
    solid = wp.loft(combine=True, ruled=False)

    out_path = str(Path(airfoil_file).with_suffix('.step'))
    cq.exporters.export(solid, out_path)
    print(f"Exported closed solid to {out_path}")

if __name__ == "__main__":
    main()
