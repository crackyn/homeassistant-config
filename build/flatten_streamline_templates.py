#!/usr/bin/env python3
"""
Flatten individual streamline-card template files into the single
streamline_templates.yaml consumed by the streamline-card frontend.

Reads every .yaml file in the streamline-cards template directory,
uses the filename (without extension) as the top-level key, indents
the file content by 2 spaces, and writes the combined result to the
streamline-card www folder.

This replicates what HA's !include_dir_named does at the Python level,
but for a frontend-loaded YAML file.

Usage:
    python build/flatten_streamline_templates.py
    python build/flatten_streamline_templates.py --templates-dir path/to/templates --out-file path/to/output.yaml
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def flatten_templates(templates_dir: Path, out_file: Path) -> None:
    if not templates_dir.is_dir():
        print(f"Error: Templates directory not found: {templates_dir}", file=sys.stderr)
        sys.exit(1)

    # Collect all .yaml files, sorted by name
    template_files = sorted(templates_dir.glob("*.yaml"))

    if not template_files:
        print(f"Warning: No .yaml files found in {templates_dir}", file=sys.stderr)
        sys.exit(0)

    parts: list[str] = []

    for filepath in template_files:
        template_name = filepath.stem
        content = filepath.read_text(encoding="utf-8").rstrip("\r\n")

        # Top-level key from filename
        lines = [f"{template_name}:"]

        # Indent each line by 2 spaces
        for line in content.split("\n"):
            if line.strip() == "":
                lines.append("")
            else:
                lines.append(f"  {line}")

        parts.append("\n".join(lines))

    output = "\n\n".join(parts) + "\n"

    # Ensure output directory exists
    out_file.parent.mkdir(parents=True, exist_ok=True)

    out_file.write_text(output, encoding="utf-8", newline="\n")

    print(f"Flattened {len(template_files)} template(s) -> {out_file}")
    for f in template_files:
        print(f"  - {f.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flatten streamline-card templates into a single YAML file."
    )
    parser.add_argument(
        "--templates-dir",
        default="ui-lovelace/templates/streamline-cards",
        help="Path to the streamline-card template directory (default: ui-lovelace/templates/streamline-cards)",
    )
    parser.add_argument(
        "--out-file",
        default="www/community/streamline-card/streamline_templates.yaml",
        help="Output file path (default: www/community/streamline-card/streamline_templates.yaml)",
    )
    args = parser.parse_args()

    # Resolve relative to repo root (parent of build/)
    repo_root = Path(__file__).resolve().parent.parent
    templates_dir = Path(args.templates_dir)
    out_file = Path(args.out_file)

    # If paths are relative, resolve from repo root
    if not templates_dir.is_absolute():
        templates_dir = repo_root / templates_dir
    if not out_file.is_absolute():
        out_file = repo_root / out_file

    flatten_templates(templates_dir, out_file)


if __name__ == "__main__":
    main()
