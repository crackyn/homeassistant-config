# Dashboard Scripts

This directory contains scripts for managing the split and flattened versions of the dashboard.

## Overview

The dashboard can exist in two forms:

1. **Split Form** (source of truth for version control):
   - `dashboard.yaml` - Main file with includes
   - `views/*.yaml` - Individual view files
   - `../../templates/button-cards/*.yaml` - Individual button card template files

2. **Flattened Form** (single file for UI editing):
   - `flattened/dashboard.yaml` - Single file with all content inline

## Scripts

### `generate_flattened_view.ps1`

**Purpose:** Flattens the split dashboard into a single file.

**Usage:**
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/generate_flattened_view.ps1
```

**What it does:**
- Reads `dashboard.yaml`
- Processes all `!include_dir_named` and `!include_dir_list` directives
- Inlines all views and button_card_templates
- Writes to `flattened/dashboard.yaml`

**When to use:**
- Before editing the dashboard in the Home Assistant UI
- To create a single-file version for backup or sharing

---

### `split_flattened_dashboard.py`

**Purpose:** Splits the flattened dashboard back into individual files.

**Usage:**
```bash
# Run directly
python scripts/split_flattened_dashboard.py

# Dry run (see what would happen)
python scripts/split_flattened_dashboard.py --dry-run

# Custom paths
python scripts/split_flattened_dashboard.py \
  --flattened path/to/dashboard.yaml \
  --views-dir path/to/views \
  --templates-dir path/to/templates
```

**What it does:**
- Reads `flattened/dashboard.yaml`
- Extracts each view and writes to `views/*.yaml`
- Extracts each button_card_template and writes to `../../templates/button-cards/*.yaml`
- Removes files that no longer exist in the flattened version
- Maintains file naming conventions

**When to use:**
- After editing the dashboard in the Home Assistant UI
- To regenerate split files from the flattened version
- To sync changes back to version control

**Requirements:**
- Python 3.7+
- PyYAML (`pip install pyyaml`)

---

### `split_flattened_dashboard.ps1`

**Purpose:** PowerShell wrapper for the Python split script.

**Usage:**
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/split_flattened_dashboard.ps1

# Dry run
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/split_flattened_dashboard.ps1 -DryRun
```

**What it does:**
- Checks for Python and PyYAML
- Installs PyYAML if missing
- Runs the Python split script

---

### `watch_flattened_dashboard.ps1`

**Purpose:** Automatically splits the flattened dashboard when it changes.

**Usage:**
```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/watch_flattened_dashboard.ps1
```

**What it does:**
- Monitors `flattened/dashboard.yaml` for changes
- Automatically runs the split script when file is modified
- Useful for real-time syncing during UI editing

**When to use:**
- When actively editing the dashboard in the Home Assistant UI
- To automatically keep split files in sync

**To stop:** Press `Ctrl+C`

---

### GitHub Action (Automatic)

**File:** `.github/workflows/split-flattened-dashboard.yml`

**Purpose:** Automatically splits the flattened dashboard when pushed to the repository.

**How it works:**
- Triggered when `flattened/dashboard.yaml` is pushed to the repository
- Runs the Python split script
- Commits the generated view and template files back to the repository
- Triggers config check and deployment

**When to use:**
- Automatic syncing when you commit changes to the flattened dashboard
- No manual action required - just commit the flattened file

**Trigger manually:**
```bash
# Via GitHub website: Actions → Split Flattened Dashboard → Run workflow
# Or push changes to the flattened dashboard file
```

---

## Typical Workflows

### Workflow 1: Edit Split Files → Flatten for UI

1. Edit individual view files in `views/` or templates in `../../templates/button-cards/`
2. Run `generate_flattened_view.ps1` to create the flattened version
3. Configure Home Assistant to use the flattened dashboard
4. View changes in the UI

```powershell
# Flatten the dashboard
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/generate_flattened_view.ps1
```

---

### Workflow 2: Edit in UI → Split for Version Control

1. Edit the dashboard in the Home Assistant UI
2. Home Assistant saves changes to `flattened/dashboard.yaml`
3. Run `split_flattened_dashboard.ps1` to regenerate split files
4. Commit the split files to version control

```powershell
# Split the dashboard
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/split_flattened_dashboard.ps1
```

---

### Workflow 3: Real-Time Sync During UI Editing

1. Start the file watcher
2. Edit the dashboard in the Home Assistant UI
3. Changes are automatically split into individual files
4. Commit changes when done

```powershell
# Start watching (press Ctrl+C to stop)
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/watch_flattened_dashboard.ps1
```

---

### Workflow 4: GitHub Action (Automated Sync)

1. Edit the dashboard in the Home Assistant UI
2. Home Assistant saves changes to `flattened/dashboard.yaml`
3. Commit and push the flattened file to Git
4. GitHub Action automatically runs split script
5. Split files are committed back to the repository

```bash
git add ui-lovelace/dashboards/my_home/flattened/dashboard.yaml
git commit -m "Update dashboard from UI"
git push
# GitHub Action automatically splits and commits the individual files
```

---

## File Naming Conventions

### Views

Views are named based on their position and type:

- `00_home.yaml` - Main home view (index 0)
- `10_main_floor.yaml` - Main floor navigation view
- `10_sv_main_floor_*.yaml` - Main floor subviews
- `20_upstairs.yaml` - Upstairs navigation view
- `20_sv_upstairs_*.yaml` - Upstairs subviews
- `30_basement.yaml` - Basement navigation view
- `30_sv_basement_*.yaml` - Basement subviews
- `40_home.yaml` - Home areas navigation view
- `40_sv_*.yaml` - Home area subviews
- `50_system.yaml` - System navigation view
- `50_sv_*.yaml` - System subviews
- `60_outside.yaml` - Outside navigation view
- `60_sv_outside_*.yaml` - Outside subviews

The numbering helps maintain view order, and `sv` indicates subviews.

### Button Card Templates

Templates are named after their template key:

- `custom_card_navigate.yaml`
- `custom_card_light.yaml`
- `custom_field_alarm_entity.yaml`
- etc.

---

## Troubleshooting

### Python not found
Install Python 3.7 or later from [python.org](https://www.python.org/)

### PyYAML not found
```bash
pip install pyyaml
```

### File encoding issues
Ensure all YAML files are UTF-8 encoded without BOM

### Script fails to find files
Run scripts from the dashboard directory (not the scripts directory):
```powershell
cd ui-lovelace/dashboards/my_home
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/split_flattened_dashboard.ps1
```

---

## Notes

- The split script intelligently handles file removal - files that no longer exist in the flattened dashboard will be deleted
- Always flatten before editing in the UI to ensure the flattened version is up-to-date
- Always split after UI editing to sync changes back to version control
- Consider using the watch script during active development for automatic syncing
