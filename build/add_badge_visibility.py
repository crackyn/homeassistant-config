"""Add a Lovelace `visibility` block to each badge entity in subview YAML files.

Rule:
- For each badge entry that has an `entity: <id>` line and does NOT already have a
  `visibility:` block, insert:

  visibility:
    - condition: state
      entity: <id>
      state_not: unavailable
    - condition: state
      entity: <id>
      state_not: unknown

This is intentionally text-based (not a YAML parser) to preserve formatting.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWS_DIR = ROOT / "ui-lovelace" / "dashboards" / "home" / "views"


def add_visibility_block(lines: list[str], *, path: Path) -> tuple[list[str], bool]:
    changed = False
    out: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)

        stripped = line.lstrip(" ")
        indent = line[: len(line) - len(stripped)]

        # Detect an `entity: ...` line inside a badge entry.
        # Badge entries here are always YAML mappings under `badges:`.
        if stripped.startswith("entity: "):
            entity_id = stripped.split("entity:", 1)[1].strip()

            # Peek ahead to see if a visibility block already exists before next badge item.
            # We scan forward until we hit a sibling-level key (`card_mod:`) or a new badge item (`- type:`)
            # or we leave the current indentation level.
            j = i + 1
            has_visibility = False
            while j < len(lines):
                nxt = lines[j]
                nxt_stripped = nxt.lstrip(" ")
                nxt_indent = nxt[: len(nxt) - len(nxt_stripped)]

                # New badge item
                if nxt_stripped.startswith("- type:") and len(nxt_indent) <= len(indent):
                    break

                # A visibility block at same level as entity/card_mod
                if nxt_stripped.startswith("visibility:") and nxt_indent == indent:
                    has_visibility = True
                    break

                # Once we hit card_mod at same level, we can insert right before it.
                if nxt_stripped.startswith("card_mod:") and nxt_indent == indent:
                    break

                j += 1

            if not has_visibility:
                # Insert visibility immediately after entity line.
                block = [
                    f"{indent}visibility:\n",
                    f"{indent}  - condition: state\n",
                    f"{indent}    entity: {entity_id}\n",
                    f"{indent}    state_not: unavailable\n",
                    f"{indent}  - condition: state\n",
                    f"{indent}    entity: {entity_id}\n",
                    f"{indent}    state_not: unknown\n",
                ]
                out.extend(block)
                changed = True

        i += 1

    return out, changed


def main() -> None:
    view_files = sorted(VIEWS_DIR.glob("sv_*.yaml"))
    if not view_files:
        raise SystemExit(f"No sv_*.yaml files found under {VIEWS_DIR}")

    updated: list[Path] = []

    for view_file in view_files:
        original = view_file.read_text(encoding="utf-8")
        lines = original.splitlines(keepends=True)
        new_lines, changed = add_visibility_block(lines, path=view_file)
        if changed:
            view_file.write_text("".join(new_lines), encoding="utf-8", newline="\n")
            updated.append(view_file)

    print(f"Processed {len(view_files)} files")
    print(f"Updated {len(updated)} files")
    for p in updated:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
