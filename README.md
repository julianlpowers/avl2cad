# AVL2STEP

Convert AVL aircraft geometry files to STEP CAD format using CadQuery.

## Installation

### From source

```bash
pip3 install -e .
```

### For development

```bash
pip3 install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Convert AVL file to STEP (output filename derived from input)
avl2step supra.avl

# Specify output filename
avl2step supra.avl output.step
```

### Python API

```python
from avl2step import convert_avl_to_step

# Convert with default settings
convert_avl_to_step("supra.avl", "supra.step")

# Include all surfaces
convert_avl_to_step("supra.avl", "supra.step", exclude_last_surface=False)

# Quiet mode
convert_avl_to_step("supra.avl", "supra.step", verbose=False)
```

## Features

- Parse AVL geometry files
- Convert airfoil sections to 3D CAD geometry
- Handle surface transformations (scale, translate, rotate)
- Support Y-axis symmetry (YDUPLICATE)
- Loft between sections to create smooth surfaces
- Export to STEP format for use in CAD software

## Requirements

- Python >= 3.8
- CadQuery >= 2.0
- NumPy >= 1.20

## License

MIT
