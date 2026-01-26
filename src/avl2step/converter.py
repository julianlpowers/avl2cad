"""Main conversion logic for AVL to STEP."""

import cadquery as cq
import math
import os
from .airfoil import load_airfoil, resample_to_reference, densify_airfoil_points
from .geometry import rot_about_te
from .avl_parser import parse_avl

RAD = math.pi / 180.0



def convert_avl_to_step(avl_path, step_path, exclude_last_surface=False, verbose=True):
    """Convert an AVL file to STEP format.
    
    Args:
        avl_path: Path to input AVL file
        step_path: Path to output STEP file
        exclude_last_surface: If True, skip the last surface (often fin/rudder)
        verbose: If True, print progress messages
        
    Returns:
        The CadQuery model object
    """
    if verbose:
        print(f"Input AVL file: {avl_path}")
        print(f"Output STEP file: {step_path}")
    
    model = None
    surfaces = parse_avl(avl_path)
    
    # Optionally exclude last surface
    surfaces_to_process = surfaces[:-1] if exclude_last_surface else surfaces
    
    for surf in surfaces_to_process:
        if verbose:
            print(f"\nBuilding: {surf['name']}")
        
        # Detect spanwise direction by checking which coordinate varies most
        sections = surf["sections"]
        if len(sections) < 2:
            continue
        
        y_range = max(sec["y"] for sec in sections) - min(sec["y"] for sec in sections)
        z_range = max(sec["z"] for sec in sections) - min(sec["z"] for sec in sections)
        
        # Determine if this is a vertical surface (spanwise in Z) or horizontal (spanwise in Y)
        is_vertical = z_range > y_range
        
        if verbose:
            if is_vertical:
                print(f"  Detected vertical surface (spanwise in Z direction)")
            else:
                print(f"  Detected horizontal surface (spanwise in Y direction)")
        
        # Choose reference airfoil ONCE per surface
        surface_ref_af = None
        for sec in surf["sections"]:
            if sec["airfoil"]:
                surface_ref_af = load_airfoil(os.path.join(os.path.dirname(avl_path), sec["airfoil"]))
                break
        if surface_ref_af is None:
            # load the default airfoil
            default_path = os.path.join(os.path.dirname(__file__), 'NACA0012.dat')
            surface_ref_af = load_airfoil(default_path)
    
        
        # Build sections
        profiles = []
        
        for sec in sections:
            if sec["airfoil"]:
                af = load_airfoil(os.path.join(os.path.dirname(avl_path), sec["airfoil"]))
            else:
                af = surface_ref_af
            
            # af = resample_to_reference(surface_ref_af, af)
            # af = densify_airfoil_points(af,1000)
            
            inc = (surf["angle"] + sec["ainc"]) * RAD
            chord = sec["c"] * surf["scale"][0]
            
            pts = []

            nidx = 1 if is_vertical else 2 # surface normal dir index
            sidx = 2 if is_vertical else 1 # spanwise dir index

            for x, n in af:
                x_new = x * chord
                n_new = n * chord
                x_new, n_new = rot_about_te((x_new, n_new), inc, chord)
                
                x_new += sec["x"] * surf["scale"][0]
                n_new += (sec["y"] if is_vertical else sec["z"]) * surf["scale"][nidx]
                
                x_new += surf["translate"][0]
                n_new += surf["translate"][nidx]
                
                pts.append((x_new, n_new))
            
            s = (sec["z"] if is_vertical else sec["y"]) * surf["scale"][sidx] + surf["translate"][sidx]
            profiles.append({'span_coord': s, 'pts': pts, 'chord': chord, 'sec_x': sec["x"]})   

            if verbose:
                if is_vertical: 
                    print(f"  section z={s:.3f}, sec_x={sec['x']:.5f}, chord={chord:.3f}, pts={len(pts)}")
                else:
                    print(f"  section y={s:.3f}, sec_x={sec['x']:.5f}, chord={chord:.3f}, pts={len(pts)}")


        # Loft the sections together
        wp = cq.Workplane("XY") if is_vertical else cq.Workplane("XZ")

        for idx, prof in enumerate(profiles):
            pts2d = [(x, n, 0) for x, n in prof['pts']]
            if idx == 0:
                offset = prof['span_coord']
            else:
                offset = prof['span_coord'] - profiles[idx-1]['span_coord']
            wp = wp.workplane(offset=offset).splineApprox(pts2d,minDeg=3).close().wire()
        solid = wp.loft(combine=True, ruled=False)
        
        
        # Handle Y-duplication (symmetry)
        if surf["ydup"] is not None:
            y0 = surf["ydup"]
            solid = solid.union(
                solid.translate((0, -y0, 0))
                     .mirror("XZ")
                     .translate((0, y0, 0))
            )
        
        # Combine with model
        if model is None:
            model = solid
        else:
            model = model.union(solid)
    
    # Export to STEP
    cq.exporters.export(model, step_path)
    
    if verbose:
        print(f"\nWrote {step_path}")
    
    return model
