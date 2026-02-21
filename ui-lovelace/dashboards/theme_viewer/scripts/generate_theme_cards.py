#!/usr/bin/env python3
"""
Generate theme viewer cards from theme_scan.json
"""
import json
import yaml
from pathlib import Path

# Get script directory and navigate to config root
script_dir = Path(__file__).parent
config_root = script_dir.parent.parent.parent.parent

# Paths
THEME_JSON = config_root / "www" / "theme_scan.json"
OUTPUT_VIEW = script_dir.parent / "views" / "00_main.yaml"

# Read theme data
with open(THEME_JSON, 'r') as f:
    data = json.load(f)
    themes = data.get('themes', {})

# Generate cards
cards = []
for theme_name in sorted(themes.keys()):
    card = {
        'type': 'custom:button-card',
        'template': 'theme_preview',
        'entity': 'sensor.raw_theme_preview',
        'variables': {
            'theme_name': theme_name
        }
    }
    cards.append(card)

# Build view structure
view = {
    'type': 'panel',
    'path': 'themes',
    'title': 'Themes',
    'cards': [
        {
            'type': 'grid',
            'title': 'Theme Previews',
            'columns': 2,
            'square': False,
            'cards': cards
        }
    ]
}

# Write output
with open(OUTPUT_VIEW, 'w', encoding='utf-8') as f:
    yaml.dump(view, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print(f"Generated {len(cards)} theme cards")
