"""Main conversion logic for AVL to STEP."""

import cadquery as cq
import math
import os
from .airfoil import load_airfoil, resample_to_reference
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
        
        for sec in sections:
            if sec["airfoil"]:
                af = load_airfoil(os.path.join(os.path.dirname(avl_path), sec["airfoil"]))
            else:
                af = surface_ref_af
            
            af = resample_to_reference(surface_ref_af, af)
            
            inc = (surf["angle"] + sec["ainc"]) * RAD
            chord = sec["c"]
            
            pts = []
            if is_vertical:
                # Vertical surface: airfoil in XY plane, loft along Z
                # For vertical surfaces, chord is scaled by scale[0] (X direction)
                scaled_chord = chord * surf["scale"][0]
                for x, y_local in af:
                    x_new = x * scaled_chord
                    y_new = y_local * scaled_chord
                    x_new, y_new = rot_about_te((x_new, y_new), inc, scaled_chord)
                    
                    x_new += sec["x"] * surf["scale"][0]
                    y_new += sec["y"] * surf["scale"][1]
                    
                    x_new += surf["translate"][0]
                    y_new += surf["translate"][1]
                    
                    pts.append((x_new, y_new))
                
                z = sec["z"] * surf["scale"][2] + surf["translate"][2]
                profiles.append({'span_coord': z, 'pts': pts, 'chord': scaled_chord, 'sec_x': sec["x"]})
                
                if verbose:
                    print(f"  section z={z:.3f}, sec_x={sec['x']:.5f}, chord={scaled_chord:.3f}, pts={len(pts)}")
            else:
                # Horizontal surface: airfoil in XZ plane, loft along Y
                # For horizontal surfaces, chord is scaled by scale[0] (X direction)
                scaled_chord = chord * surf["scale"][0]
                for x, z_local in af:
                    x_new = x * scaled_chord
                    z_new = z_local * scaled_chord
                    x_new, z_new = rot_about_te((x_new, z_new), inc, scaled_chord)
                    
                    x_new += sec["x"] * surf["scale"][0]
                    z_new += sec["z"] * surf["scale"][2]
                    
                    x_new += surf["translate"][0]
                    z_new += surf["translate"][2]
                    
                    pts.append((x_new, z_new))
                
                y = sec["y"] * surf["scale"][1] + surf["translate"][1]
                profiles.append({'span_coord': y, 'pts': pts, 'chord': scaled_chord, 'sec_x': sec["x"]})
                
                if verbose:
                    print(f"  section y={y:.3f}, sec_x={sec['x']:.5f}, chord={scaled_chord:.3f}, pts={len(pts)}")
        
        # Loft section by section (pairwise)
        surface_solid = None
        for i in range(len(profiles) - 1):
            prof1 = profiles[i]
            prof2 = profiles[i + 1]
            
            d_span = prof2['span_coord'] - prof1['span_coord']
            
            if is_vertical:
                # Vertical surface: loft in XY plane along Z axis
                wp = cq.Workplane("XY")
                wp = wp.workplane(offset=prof1['span_coord']).polyline(prof1['pts']).close()
                wp = wp.workplane(offset=d_span).polyline(prof2['pts']).close()
            else:
                # Horizontal surface: loft in XZ plane along Y axis
                wp = cq.Workplane("XZ")
                wp = wp.workplane(offset=prof1['span_coord']).polyline(prof1['pts']).close()
                wp = wp.workplane(offset=d_span).polyline(prof2['pts']).close()
            
            segment = wp.loft(combine=True)
            
            if surface_solid is None:
                surface_solid = segment
            else:
                surface_solid = surface_solid.union(segment)
            
            if verbose:
                coord_name = 'z' if is_vertical else 'y'
                print(f"  lofted segment {i}: {coord_name}={prof1['span_coord']:.3f} to {prof2['span_coord']:.3f}")
        
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
