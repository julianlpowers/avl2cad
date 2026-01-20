#!/usr/bin/env python3
"""
Test script for vertical surface (fin) conversion from AVL to STEP.

This test validates that the generated STEP file has correct:
- Chord dimensions at each section height
- Section positions (Y=0 for all sections, varying Z heights)
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


def measure_chord_at_z(shape, z_value, tolerance=0.01):
    """
    Measure the chord (X extent) at a given Z coordinate by sectioning the geometry.
    
    For vertical surfaces (fins), sections are stacked along the Z axis.
    
    Args:
        shape: OCP shape object
        z_value: Z coordinate to measure at
        tolerance: Tolerance for finding points
        
    Returns:
        dict with x_min, x_max, chord, or None if no section found
    """
    # Create a plane perpendicular to Z axis at z_value
    plane = gp_Pln(gp_Pnt(0, 0, z_value), gp_Dir(0, 0, 1))
    
    # Perform section
    section = BRepAlgoAPI_Section(shape, plane)
    section.Build()
    
    if not section.IsDone():
        return None
    
    section_shape = section.Shape()
    
    # Explore vertices in the section to get all points
    explorer = TopExp_Explorer(section_shape, TopAbs_VERTEX)
    
    all_x_coords = []
    all_y_coords = []
    
    while explorer.More():
        vertex = TopoDS.Vertex_s(explorer.Current())
        pnt = BRep_Tool.Pnt_s(vertex)
        all_x_coords.append(pnt.X())
        all_y_coords.append(pnt.Y())
        explorer.Next()
    
    if not all_x_coords:
        return None
    
    x_min = min(all_x_coords)
    x_max = max(all_x_coords)
    chord = x_max - x_min
    
    return {
        'x_min': x_min,
        'x_max': x_max,
        'chord': chord,
        'y_coords': all_y_coords,
        'num_points': len(all_x_coords)
    }


def test_file_exists(step_file):
    """Test 1: Check if STEP file was created."""
    if not os.path.exists(step_file):
        print(f"❌ FAIL: STEP file not found: {step_file}")
        return False
    print(f"✓ PASS: STEP file exists: {step_file}")
    return True


def test_file_loadable(step_file):
    """Test 2: Check if STEP file can be loaded."""
    try:
        model = cq.importers.importStep(str(step_file))
        print(f"✓ PASS: STEP file loads successfully")
        return True, model
    except Exception as e:
        print(f"❌ FAIL: Could not load STEP file: {e}")
        return False, None


def test_chord_dimensions(shape, avl_file):
    """Test 3: Check chord dimensions at each section height."""
    # Parse AVL to get expected values
    surfaces = parse_avl(avl_file)
    
    if not surfaces:
        print("❌ FAIL: No surfaces found in AVL file")
        return False
    
    surf = surfaces[0]
    
    # For vertical surfaces (fin), sections have varying Z but constant Y=0
    # The converter lofts along the Z axis
    # SCALE: (1.15, 1.15, 1.1)
    # TRANSLATE: (42.5, 0.0, 0.0)
    # Sections are at z=0, 9.0, 11.25, 12.0
    # After scaling by scale[2]=1.1, Z positions become: 0, 9.9, 12.375, 13.2
    # Chords are scaled by scale[0]=1.15
    expected_sections = [
        {'z': 0.0 * 1.1 + 0.0, 'chord': 7.0 * 1.15, 'x_offset': 0.0},
        {'z': 9.0 * 1.1 + 0.0, 'chord': 4.0 * 1.15, 'x_offset': 1.125},
        {'z': 11.25 * 1.1 + 0.0, 'chord': 2.8333 * 1.15, 'x_offset': 1.875},
        {'z': 12.0 * 1.1 + 0.0, 'chord': 2.0 * 1.15, 'x_offset': 2.5},
    ]
    
    all_passed = True
    tolerance = 0.1  # Allow 0.1 unit tolerance
    
    for i, expected in enumerate(expected_sections):
        result = measure_chord_at_z(shape, expected['z'])
        
        if result is None:
            print(f"❌ FAIL: No section found at z={expected['z']:.3f}")
            all_passed = False
            continue
        
        chord_diff = abs(result['chord'] - expected['chord'])
        
        if chord_diff > tolerance:
            print(f"❌ FAIL: Section {i} at z={expected['z']:.3f}")
            print(f"    Expected chord: {expected['chord']:.3f}")
            print(f"    Measured chord: {result['chord']:.3f}")
            print(f"    Difference: {chord_diff:.3f}")
            all_passed = False
        else:
            print(f"✓ PASS: Section {i} at z={expected['z']:.3f}, chord={result['chord']:.3f} "
                  f"(expected {expected['chord']:.3f})")
    
    return all_passed


def test_y_position(shape, avl_file):
    """Test 4: Verify all sections are centered at Y≈0 with correct thickness."""
    # Parse AVL to get chord information
    surfaces = parse_avl(avl_file)
    surf = surfaces[0]
    
    # NACA0012 is 12% thick
    thickness_ratio = 0.12
    
    # For vertical surfaces, all sections should be centered around Y≈0
    # The airfoil thickness in Y should be approximately 12% of chord
    # Sample at a few Z heights
    test_positions = [
        {'z': 0.0 * 1.1, 'chord': 7.0 * 1.15},
        {'z': 9.0 * 1.1, 'chord': 4.0 * 1.15},
        {'z': 11.25 * 1.1, 'chord': 2.8333 * 1.15},
        {'z': 12.0 * 1.1, 'chord': 2.0 * 1.15},
    ]
    
    all_passed = True
    
    for pos in test_positions:
        result = measure_chord_at_z(shape, pos['z'])
        
        if result is None:
            continue
        
        # Check that Y coordinates are centered around 0
        if result['y_coords']:
            y_min = min(result['y_coords'])
            y_max = max(result['y_coords'])
            y_center = (y_min + y_max) / 2
            y_thickness = y_max - y_min
            
            expected_thickness = pos['chord'] * thickness_ratio
            center_tolerance = 0.01
            thickness_tolerance = expected_thickness * 0.2  # 20% tolerance
            
            # Check centered at Y=0
            if abs(y_center) > center_tolerance:
                print(f"❌ FAIL: Y center at z={pos['z']:.3f}: expected≈0.0, got={y_center:.6f}")
                all_passed = False
            else:
                print(f"✓ PASS: Y centered at z={pos['z']:.3f} (center={y_center:.6f})")
            
            # Check thickness is approximately 12% of chord
            thickness_diff = abs(y_thickness - expected_thickness)
            if thickness_diff > thickness_tolerance:
                print(f"❌ FAIL: Y thickness at z={pos['z']:.3f}: expected≈{expected_thickness:.3f}, got={y_thickness:.3f}")
                all_passed = False
            else:
                print(f"✓ PASS: Y thickness at z={pos['z']:.3f} is {y_thickness:.3f} (expected≈{expected_thickness:.3f})")
    
    return all_passed


def test_x_translation(shape):
    """Test 5: Verify X translation is applied (TRANSLATE 42.5 0.0 0.0)."""
    # Check section at z=0
    result = measure_chord_at_z(shape, 0.0)
    
    if result is None:
        print("❌ FAIL: Could not measure X position")
        return False
    
    expected_x_translate = 42.5
    tolerance = 0.5
    
    # The leading edge at z=0 should be at approximately x=42.5
    # Since chord is 7.0 * 1.15 = 8.05, leading edge should be around 42.5
    x_min = result['x_min']
    
    diff = abs(x_min - expected_x_translate)
    
    if diff > tolerance:
        print(f"❌ FAIL: X translation incorrect")
        print(f"    Expected x_min near: {expected_x_translate:.3f}")
        print(f"    Measured x_min: {x_min:.3f}")
        print(f"    Difference: {diff:.3f}")
        return False
    else:
        print(f"✓ PASS: X translation correct (x_min={x_min:.3f}, expected≈{expected_x_translate:.3f})")
        return True


def main():
    """
    Main test function that runs all subtests.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("=" * 70)
    print("VERTICAL SURFACE (FIN) CONVERSION TEST")
    print("=" * 70)
    
    # Get file paths
    test_dir = Path(__file__).parent
    avl_file = test_dir / "vert.avl"
    step_file = test_dir / "vert.step"
    
    # Convert AVL to STEP
    print(f"\nConverting {avl_file} to {step_file}...")
    try:
        convert_avl_to_step(str(avl_file), str(step_file), exclude_last_surface=False, verbose=False)
        print("✓ Conversion completed\n")
    except Exception as e:
        print(f"❌ Conversion failed: {e}\n")
        return False
    
    # Run tests
    test_results = []
    
    # Test 1: File exists
    print("\n--- Test 1: File Exists ---")
    test_results.append(test_file_exists(step_file))
    
    if not test_results[-1]:
        print("\n" + "=" * 70)
        print("OVERALL RESULT: FAILED (file not created)")
        print("=" * 70)
        return False
    
    # Test 2: File loadable
    print("\n--- Test 2: File Loadable ---")
    passed, model = test_file_loadable(step_file)
    test_results.append(passed)
    
    if not passed:
        print("\n" + "=" * 70)
        print("OVERALL RESULT: FAILED (file not loadable)")
        print("=" * 70)
        return False
    
    # Get the shape
    if hasattr(model, 'val'):
        shape = model.val().wrapped
    elif hasattr(model, 'wrapped'):
        shape = model.wrapped
    else:
        shape = model
    
    # Test 3: Chord dimensions
    print("\n--- Test 3: Chord Dimensions ---")
    test_results.append(test_chord_dimensions(shape, avl_file))
    
    # Test 4: Y position (should be 0 for vertical surface)
    print("\n--- Test 4: Y Position (Vertical) ---")
    test_results.append(test_y_position(shape, avl_file))
    
    # Test 5: X translation
    print("\n--- Test 5: X Translation ---")
    test_results.append(test_x_translation(shape))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    total_tests = len(test_results)
    passed_tests = sum(test_results)
    
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Failed: {total_tests - passed_tests}/{total_tests}")
    
    all_passed = all(test_results)
    
    if all_passed:
        print("\n✓ OVERALL RESULT: ALL TESTS PASSED")
    else:
        print("\n❌ OVERALL RESULT: SOME TESTS FAILED")
    
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
