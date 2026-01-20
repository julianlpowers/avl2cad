#!/usr/bin/env python3
"""Command-line interface for avl2step converter."""

import sys
import os
from avl2step.converter import convert_avl_to_step


def main():
    """Main entry point for the avl2step command."""
    if len(sys.argv) < 2:
        print("Usage: avl2step <input.avl> [output.step]")
        print("  If output.step is not specified, it will be derived from input filename")
        sys.exit(1)
    
    avl_path = sys.argv[1]
    
    if len(sys.argv) >= 3:
        step_path = sys.argv[2]
    else:
        # Derive output filename from input: fnm.avl -> fnm.step
        base_name = os.path.splitext(avl_path)[0]
        step_path = base_name + ".step"
    
    try:
        convert_avl_to_step(avl_path, step_path, verbose=True)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
