# avl2step Test Suite

This directory contains comprehensive test suites for the avl2step converter.

## Running Tests

### Run All Tests
```bash
./run_all_tests.sh
```

This will automatically discover and run all test suites in subdirectories.

### Run Individual Tests
```bash
cd TEST_vertical_surface
python3 TEST.py
```

```bash
cd TEST_horizontal_surface
python3 TEST.py
```

## Test Suites

### TEST_vertical_surface
Tests conversion of vertical surfaces (fins, rudders, vertical stabilizers).

**Test File:** `vert.avl` - A simple fin with 4 sections spanning vertically (Z direction)

**Validations:**
1. File creation
2. Geometry loading
3. Chord dimensions at 4 height positions (Z axis)
4. Y position (constant for vertical surfaces) and airfoil thickness
5. X translation accuracy

**Key Characteristics:**
- Sections vary in Z coordinate (vertical)
- Y coordinate is constant (0.0)
- Airfoil profiles lie in XY plane
- Lofted along Z axis

### TEST_horizontal_surface
Tests conversion of horizontal surfaces (wings, horizontal stabilizers).

**Test File:** `horiz.avl` - A simple tapered wing with 4 sections spanning laterally (Y direction)

**Validations:**
1. File creation
2. Geometry loading
3. Chord dimensions at 4 spanwise positions (Y axis)
4. Z position (constant for horizontal surfaces) and airfoil thickness
5. X translation accuracy

**Key Characteristics:**
- Sections vary in Y coordinate (spanwise)
- Z coordinate is constant (0.0 in AVL, translated to 2.0)
- Airfoil profiles lie in XZ plane
- Lofted along Y axis (note: CadQuery XZ workplane offset moves in -Y direction)

## Expected Results

All test suites should return:
- Exit code 0 on success
- Exit code 1 on failure
- Boolean `True` return value from `main()` on success

Each test suite runs 5 sub-tests and reports:
```
OVERALL RESULT: ALL TESTS PASSED
Passed: 5/5, Failed: 0/5
```

## Test Architecture

Each test suite consists of:
- `*.avl` - Input AVL geometry file
- `TEST.py` - Python test script with 5 comprehensive tests
- `*.step` - Generated STEP file (created during test run)

### Common Test Structure

1. **File Exists** - Verify STEP file was created
2. **Surface Exists** - Verify geometry can be loaded
3. **Chord Dimensions** - Measure and validate chord lengths at each section
4. **Position & Thickness** - Verify constant coordinate and airfoil thickness (12% for NACA0012)
5. **Translation** - Verify X translation is applied correctly

### Measurement Technique

Tests use OpenCascade (OCP) to section the geometry perpendicular to the lofting axis:
- **Vertical surfaces**: Section with XY planes at different Z heights
- **Horizontal surfaces**: Section with XZ planes at different Y positions

This provides precise chord measurements and validates geometric accuracy.

## Adding New Tests

To add a new test suite:

1. Create a new directory: `TEST_<name>/`
2. Add an AVL file: `<name>.avl`
3. Create `TEST.py` following the pattern in existing tests
4. Make sure `main()` returns `True` on success
5. Run `./run_all_tests.sh` to verify

The test runner will automatically discover and execute your new test.
