"""Main conversion logic for AVL to STEP."""

import cadquery as cq
import math
import os
from .airfoil import load_airfoil, resample_to_reference
from .geometry import rot_about_te
from .avl_parser import parse_avl

RAD = math.pi / 180.0


def convert_avl_to_step(avl_path, step_path, exclude_last_surface=True, verbose=True):
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
        
        # Choose reference airfoil ONCE per surface
        surface_ref_af = None
        for sec in surf["sections"]:
            if sec["airfoil"]:
                surface_ref_af = load_airfoil(os.path.join(os.path.dirname(avl_path), sec["airfoil"]))
                break
        if surface_ref_af is None:
            # Try to load a default airfoil
            # default_path = os.path.join(os.path.dirname(avl_path), 'NACA0012.dat')
            default_path = os.path.join(os.path.dirname(__file__), 'NACA0012.dat')
            if os.path.exists(default_path):
                surface_ref_af = load_airfoil(default_path)
            else:
                # Fall back to flat plate
                from .airfoil import flat_plate
                surface_ref_af = flat_plate()
        
        # Build sections
        profiles = []
        
        for sec in surf["sections"]:
            if sec["airfoil"]:
                af = load_airfoil(os.path.join(os.path.dirname(avl_path), sec["airfoil"]))
            else:
                af = surface_ref_af
            
            af = resample_to_reference(surface_ref_af, af)
            
            inc = (surf["angle"] + sec["ainc"]) * RAD
            chord = sec["c"]
            
            pts = []
            for x, z in af:
                x *= chord
                z *= chord
                x, z = rot_about_te((x, z), inc, chord)
                
                x += sec["x"] * surf["scale"][0]
                z += sec["z"] * surf["scale"][2]
                
                x += surf["translate"][0]
                z += surf["translate"][2]
                
                pts.append((x, z))
            
            y = sec["y"] * surf["scale"][1] + surf["translate"][1]
            
            profiles.append({'y': y, 'pts': pts, 'chord': chord, 'sec_x': sec["x"]})
            
            if verbose:
                print(f"  section y={y:.3f}, sec_x={sec['x']:.5f}, chord={chord:.3f}, pts={len(pts)}")
        
        # Loft section by section (pairwise)
        surface_solid = None
        for i in range(len(profiles) - 1):
            prof1 = profiles[i]
            prof2 = profiles[i + 1]
            
            dy = prof2['y'] - prof1['y']
            
            wp = cq.Workplane("XZ")
            wp = wp.workplane(offset=prof1['y']).polyline(prof1['pts']).close()
            wp = wp.workplane(offset=dy).polyline(prof2['pts']).close()
            
            segment = wp.loft(combine=True)
            
            if surface_solid is None:
                surface_solid = segment
            else:
                surface_solid = surface_solid.union(segment)
            
            if verbose:
                print(f"  lofted segment {i}: y={prof1['y']:.3f} to y={prof2['y']:.3f}")
        
        solid = surface_solid
        
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
