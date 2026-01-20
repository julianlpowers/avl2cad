# Horizontal Surface Test

This test validates the conversion of horizontal surfaces (wings, horizontal stabilizers) from AVL to STEP format.

## Test File
- `horiz.avl` - AVL file defining a simple tapered wing with 4 sections
- `TEST.py` - Test suite with 5 comprehensive tests
- `horiz.step` - Generated STEP file (created by running the test)

## What It Tests

### Test 1: File Exists
Verifies that the STEP file is created successfully.

### Test 2: Surface Exists
Verifies that the STEP file can be loaded and contains valid geometry.

### Test 3: Chord Dimensions
Validates that chord lengths are correct at each spanwise section:
- Root (y=0): 8.050 units
- Section 1 (y=3.45): 4.600 units  
- Section 2 (y=5.175): 3.258 units
- Tip (y=5.75): 2.300 units

### Test 4: Z Position (Horizontal)
Validates that:
- Z coordinate is constant for all sections (horizontal surface)
- Z center = 2.0 (from TRANSLATE)
- Airfoil thickness = 12% of chord (NACA0012)

### Test 5: X Translation
Validates that the X leading edge position is correctly translated by 5.0 units.

## Running the Test

```bash
cd tests/TEST_horizontal_surface
python3 TEST.py
```

The test returns `True` (exit code 0) if all tests pass, `False` (exit code 1) otherwise.

## Important Note

CadQuery's XZ workplane has its normal pointing in the -Y direction. This means that when lofting horizontal surfaces with `workplane(offset=y)`, the geometry is actually positioned at Y = -offset. The test accounts for this by using negative Y values when measuring sections.
