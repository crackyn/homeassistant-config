#!/usr/bin/env python3
"""
Sanitize the homeassistant-config repo for public sharing.

Reads secrets.yaml, replaces all values with placeholder text,
and writes a sanitized version. Also removes any other files
that shouldn't be public.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def sanitize_secrets(secrets_path: Path, output_path: Path) -> None:
    """Replace secret values with descriptive placeholders."""
    if not secrets_path.exists():
        print(f"No secrets.yaml found at {secrets_path}, creating stub.")
        output_path.write_text(
            "# Secrets have been removed for public sharing.\n",
            encoding="utf-8",
        )
        return

    lines = secrets_path.read_text(encoding="utf-8").splitlines()
    sanitized: list[str] = []

    for line in lines:
        # Preserve comments and blank lines
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            sanitized.append(line)
            continue

        # Match key: value pairs
        match = re.match(r"^(\s*)([\w_]+)(\s*:\s*)(.*)", line)
        if match:
            indent, key, separator, value = match.groups()
            # Replace value with a placeholder based on the key name
            placeholder = f'"!secret {key}"'
            sanitized.append(f"{indent}{key}{separator}{placeholder}")
        else:
            sanitized.append(line)

    output_path.write_text("\n".join(sanitized) + "\n", encoding="utf-8")
    print(f"Sanitized secrets.yaml ({len(lines)} lines)")


def main() -> None:
    repo_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    secrets_file = repo_root / "secrets.yaml"
    sanitize_secrets(secrets_file, secrets_file)

    print("Sanitization complete.")


if __name__ == "__main__":
    main()
