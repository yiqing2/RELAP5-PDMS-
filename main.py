"""PDMS to RELAP5 Input Card Automatic Conversion and Diagram Generation.

Usage:
    python main.py                        Launch GUI (default)
    python main.py --gui                  Launch GUI
    python main.py <pdms_export.txt> [options]   CLI mode

CLI Options:
    --boundary, -b FILE     Boundary configuration CSV (default: auto-detect)

    -h, --help              Show this help message

Pipeline: Parse -> Build Graph -> Assign IDs -> Configure Boundaries
          -> Write RELAP5 Deck -> Generate Diagrams
"""

import argparse
import os
import sys
from pathlib import Path

def run_cli(args):

    print("PDMS to RELAP5 Converter — skeleton framework ready.")
    print(f"  Input:        {args.input}")
    print(f"  Output dir:   {args.output_dir}")



def run_gui():
    """Launch the Tkinter GUI."""
    from src.gui.main_window import launch_gui
    launch_gui()

def main():
    """Main entry point. GUI by default; CLI when a file argument is given."""

    # --- GUI mode: no arguments, or explicit --gui flag ---
    if len(sys.argv) == 1 or "--gui" in sys.argv:
        run_gui()
        return

    # --- CLI mode ---
    parser = argparse.ArgumentParser(
        description="PDMS to RELAP5 Input Deck Converter with Diagram Generation"
    )
    parser.add_argument("input", nargs="?", help="PDMS export text file")
    parser.add_argument("--gui", action="store_true",
                        help="Launch GUI mode (default when no arguments)")
    parser.add_argument("--boundary", "-b", default=None,
                        help="Boundary configuration CSV file")
    parser.add_argument("--output-dir", "-o", default="./output",
                        help="Output directory (default: ./output)")


    args = parser.parse_args()

    if args.gui or args.input is None:
        run_gui()
        return

    run_cli(args)

if __name__ == "__main__":
    main()
