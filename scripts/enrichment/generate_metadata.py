#!/usr/bin/env python3

"""
Knowledge Enrichment Generator

Future responsibility:

- Read _tools/
- Produce _data/tool-metadata/

No implementation yet.

This file intentionally contains only the project contract.
"""

from pathlib import Path

TOOLS_DIR = Path("_tools")
OUTPUT_DIR = Path("_data/tool-metadata")


def main():
    print("Knowledge enrichment pipeline (planned)")
    print(f"Tools: {TOOLS_DIR}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
