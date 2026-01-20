#!/usr/bin/env python3
"""
Test script for horizontal surface (wing) conversion from AVL to STEP.

This test validates that the generated STEP file has correct:
- Chord dimensions at each section spanwise position
- Section positions (Z constant, varying Y positions)
- Proper scaling and translation
- Surface exists and is valid
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import avl2step
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from avl2step import convert_avl_to_step, parse_avl
import cadquery as cq
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_VERTEX
from OCP.TopoDS import TopoDS
from OCP.BRep import BRep_Tool


def measure_chord_at_y(shape, y_value, tolerance=0.01):
    """
    Measure the chord (X extent) at a given Y coordinate by sectioning the geometry.
    
    For horizontal surfaces (wings), sections are stacked along the Y axis.
    
    Args:
        shape: OCP shape object
        y_value: Y coordinate to measure at
        tolerance: Tolerance for finding points
        
    Returns:
        dict with x_min, x_max, chord, or None if no section found
    """
    # Create a plane perpendicular to Y axis at y_value
    plane = gp_Pln(gp_Pnt(0, y_value, 0), gp_Dir(0, 1, 0))
    
    # Perform section
    section = BRepAlgoAPI_Section(shape, plane)
    section.Build()
    
    if not section.IsDone():
        return None
    
    section_shape = section.Shape()
    
    # Extract vertices from the section
    explorer = TopExp_Explorer(section_shape, TopAbs_VERTEX)
    
    x_coords = []
    z_coords = []
    
    while explorer.More():
        vertex = TopoDS.Vertex_s(explorer.Current())
        pnt = BRep_Tool.Pnt_s(vertex)
        x_coords.append(pnt.X())
        z_coords.append(pnt.Z())
        explorer.Next()
    
    if not x_coords:
        return None
    
    x_min = min(x_coords)
    x_max = max(x_coords)
    z_min = min(z_coords)
    z_max = max(z_coords)
    chord = x_max - x_min
    
    return {
        'x_min': x_min,
        'x_max': x_max,
        'chord': chord,
        'z_min': z_min,
        'z_max': z_max,
        'z_center': (z_min + z_max) / 2.0,
        'z_thickness': z_max - z_min
    }


def test_file_exists():
    """Test 1: Verify the STEP file was created"""
    print("\n--- Test 1: File Exists ---")
    step_file = Path(__file__).parent / "horiz.step"
    
    if not step_file.exists():
        print(f"✗ FAIL: STEP file not found at {step_file}")
        return False
    
    print(f"✓ PASS: STEP file exists at {step_file}")
    return True


def test_surface_exists():
    """Test 2: Verify the surface can be loaded and has geometry"""
    print("\n--- Test 2: Surface Exists ---")
    step_file = Path(__file__).parent / "horiz.step"
    
    try:
        imported = cq.importers.importStep(str(step_file))
        
        if imported is None:
            print("✗ FAIL: Could not import STEP file")
            return False
        
        # Get the OCP shape from the CadQuery object
        shape = imported.val().wrapped
        
        if shape is None or shape.IsNull():
            print("✗ FAIL: Shape is null")
            return False
        
        print(f"✓ PASS: Surface loaded successfully")
        return True
        
    except Exception as e:
        print(f"✗ FAIL: Exception loading surface: {e}")
        return False


def test_chord_dimensions():
    """Test 3: Verify chord dimensions at each section"""
    print("\n--- Test 3: Chord Dimensions ---")
    
    # Expected values from AVL file:
    # SCALE: 1.15 1.15 1.1
    # Sections at Y positions (after scaling by scale[1]=1.15):
    #   Section 0: Y=0.0*1.15=0.0,     chord=7.0*1.15=8.050
    #   Section 1: Y=3.0*1.15=3.45,    chord=4.0*1.15=4.600
    #   Section 2: Y=4.5*1.15=5.175,   chord=2.8333*1.15=3.258
    #   Section 3: Y=5.0*1.15=5.75,    chord=2.0*1.15=2.300
    # 
    # NOTE: CadQuery XZ workplane offset moves in -Y direction, so actual Y values are negative
    
    expected_sections = [
        {'y': -0.0, 'chord': 8.050},
        {'y': -3.45, 'chord': 4.600},
        {'y': -5.175, 'chord': 3.258},
        {'y': -5.75, 'chord': 2.300},
    ]
    
    step_file = Path(__file__).parent / "horiz.step"
    imported = cq.importers.importStep(str(step_file))
    shape = imported.val().wrapped
    
    all_passed = True
    tolerance = 0.05  # 5% tolerance for chord measurements
    
    for i, expected in enumerate(expected_sections):
        y_val = expected['y']
        expected_chord = expected['chord']
        
        result = measure_chord_at_y(shape, y_val)
        
        if result is None:
            print(f"✗ FAIL: Section {i} at y={y_val:.3f} - no geometry found")
            all_passed = False
            continue
        
        measured_chord = result['chord']
        error = abs(measured_chord - expected_chord)
        error_pct = (error / expected_chord) * 100
        
        if error_pct <= tolerance * 100:
            print(f"✓ PASS: Section {i} at y={y_val:.3f}, chord={measured_chord:.3f} (expected {expected_chord:.3f})")
        else:
            print(f"✗ FAIL: Section {i} at y={y_val:.3f}, chord={measured_chord:.3f} (expected {expected_chord:.3f}, error={error_pct:.1f}%)")
            all_passed = False
    
    return all_passed


def test_z_position():
    """Test 4: Verify Z position is constant (horizontal surface) and airfoil thickness"""
    print("\n--- Test 4: Z Position (Horizontal) ---")
    
    # For horizontal surfaces, Z should be constant (translate[2]=2.0 after scaling)
    # All sections have Zle=0.0, so after scale[2]=1.1 and translate=2.0: Z = 0.0*1.1 + 2.0 = 2.0
    expected_z = 2.0
    
    # NACA0012 airfoil is symmetric, 12% thick
    # Thickness in Z direction = chord * 0.12
    
    # NOTE: CadQuery XZ workplane offset moves in -Y direction, so actual Y values are negative
    test_positions = [
        {'y': -0.0, 'chord': 8.050},
        {'y': -3.45, 'chord': 4.600},
        {'y': -5.175, 'chord': 3.258},
        {'y': -5.75, 'chord': 2.300},
    ]
    
    step_file = Path(__file__).parent / "horiz.step"
    imported = cq.importers.importStep(str(step_file))
    shape = imported.val().wrapped
    
    all_passed = True
    z_tolerance = 0.1  # Absolute tolerance for Z position
    thickness_tolerance = 0.20  # 20% tolerance for thickness
    
    for i, pos in enumerate(test_positions):
        y_val = pos['y']
        chord = pos['chord']
        expected_thickness = chord * 0.12
        
        result = measure_chord_at_y(shape, y_val)
        
        if result is None:
            print(f"✗ FAIL: Section {i} at y={y_val:.3f} - no geometry found")
            all_passed = False
            continue
        
        z_center = result['z_center']
        z_thickness = result['z_thickness']
        
        # Check Z center position
        z_error = abs(z_center - expected_z)
        if z_error <= z_tolerance:
            print(f"✓ PASS: Z centered at y={y_val:.3f} (center={z_center:.6f})")
        else:
            print(f"✗ FAIL: Z not centered at y={y_val:.3f} (center={z_center:.6f}, expected≈{expected_z:.3f})")
            all_passed = False
        
        # Check airfoil thickness
        thickness_error = abs(z_thickness - expected_thickness) / expected_thickness
        if thickness_error <= thickness_tolerance:
            print(f"✓ PASS: Z thickness at y={y_val:.3f} is {z_thickness:.3f} (expected≈{expected_thickness:.3f})")
        else:
            print(f"✗ FAIL: Z thickness at y={y_val:.3f} is {z_thickness:.3f} (expected≈{expected_thickness:.3f}, error={thickness_error*100:.1f}%)")
            all_passed = False
    
    return all_passed


def test_x_translation():
    """Test 5: Verify X translation is correct"""
    print("\n--- Test 5: X Translation ---")
    
    # TRANSLATE: 5.0 0.0 2.0
    # First section has Xle=0.0, so after translation: X_leading_edge = 0.0 + 5.0 = 5.0
    expected_x_le = 5.0
    
    step_file = Path(__file__).parent / "horiz.step"
    imported = cq.importers.importStep(str(step_file))
    shape = imported.val().wrapped
    
    # Measure at root (y=0.0)
    result = measure_chord_at_y(shape, 0.0)
    
    if result is None:
        print("✗ FAIL: Could not measure root section")
        return False
    
    x_min = result['x_min']
    tolerance = 0.1  # Absolute tolerance
    
    error = abs(x_min - expected_x_le)
    if error <= tolerance:
        print(f"✓ PASS: X translation correct (x_min={x_min:.3f}, expected≈{expected_x_le:.3f})")
        return True
    else:
        print(f"✗ FAIL: X translation incorrect (x_min={x_min:.3f}, expected≈{expected_x_le:.3f})")
        return False


def main():
    """Run all tests and return True if all pass"""
    
    # First, convert the AVL file to STEP
    print("Converting horiz.avl to horiz.step...")
    avl_file = Path(__file__).parent / "horiz.avl"
    step_file = Path(__file__).parent / "horiz.step"
    
    try:
        convert_avl_to_step(str(avl_file), str(step_file), exclude_last_surface=False)
        print(f"Conversion complete: {step_file}")
    except Exception as e:
        print(f"ERROR: Conversion failed: {e}")
        return False
    
    # Run all tests
    tests = [
        ("File Exists", test_file_exists),
        ("Surface Exists", test_surface_exists),
        ("Chord Dimensions", test_chord_dimensions),
        ("Z Position (Horizontal)", test_z_position),
        ("X Translation", test_x_translation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("OVERALL RESULT:", end=" ")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    if passed_count == total_count:
        print("ALL TESTS PASSED")
        print(f"Passed: {passed_count}/{total_count}, Failed: {total_count - passed_count}/{total_count}")
        return True
    else:
        print("SOME TESTS FAILED")
        print(f"Passed: {passed_count}/{total_count}, Failed: {total_count - passed_count}/{total_count}")
        print("\nFailed tests:")
        for test_name, passed in results:
            if not passed:
                print(f"  - {test_name}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
