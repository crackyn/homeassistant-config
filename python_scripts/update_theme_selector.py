# Auto-detect themes from /config/themes and push them into an input_select
# Also build a palette preview sensor attribute per theme

import os
import yaml

themes_path = "/config/themes"
theme_names = []
theme_colors = {}

for filename in os.listdir(themes_path):
    if filename.endswith(".yaml") or filename.endswith(".yml"):
        try:
            with open(os.path.join(themes_path, filename), "r") as f:
                data = yaml.safe_load(f) or {}
                # Each YAML file may define multiple themes
                if isinstance(data, dict):
                    for theme, values in data.items():
                        theme_names.append(theme)
                        if isinstance(values, dict):
                            theme_colors[theme] = {
                                "primary-color": values.get("primary-color", "#000000"),
                                "accent-color": values.get("accent-color", "#000000"),
                                "primary-background-color": values.get("primary-background-color", "#000000"),
                                "card-background-color": values.get("card-background-color", "#000000"),
                            }
        except Exception as e:
            logger.error(f"Error reading theme file {filename}: {e}")

if not theme_names:
    theme_names = ["Default"]

# Update selector
hass.services.call(
    "input_select",
    "set_options",
    {"entity_id": "input_select.theme_selector", "options": theme_names},
    False,
)

# Update preview sensor
hass.states.set(
    "sensor.theme_previews",
    ",".join(theme_names),
    {"themes": theme_colors},
)
