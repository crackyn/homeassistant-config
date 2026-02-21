import os, yaml, json
import re

themes_path = "/config/themes"
output_file = "/config/www/theme_scan.json"

def resolve_var(value, theme_data, visited=None):
    """Recursively resolve CSS var() references to actual values."""
    if visited is None:
        visited = set()
    
    # If not a string or doesn't contain var(), return as-is
    if not isinstance(value, str) or "var(" not in value:
        return value
    
    # Extract variable name from var(--variable-name)
    match = re.search(r'var\(--([^)]+)\)', value)
    if not match:
        return value
    
    var_name = match.group(1)
    
    # Check for circular references
    if var_name in visited:
        return "#808080"  # Return gray for circular references
    
    visited.add(var_name)
    
    # Look up the variable in theme data (try with and without -- prefix)
    resolved = theme_data.get(var_name) or theme_data.get(f"--{var_name}")
    
    if resolved:
        # Recursively resolve in case the value is another var()
        return resolve_var(resolved, theme_data, visited)
    
    # If not found, return gray as fallback
    return "#808080"

def extract_colors_for_mode(mode_data):
    """Extract and resolve 4 key colors from mode data."""
    return {
        "primary-color": resolve_var(mode_data.get("primary-color", 
                                     mode_data.get("m3-primary", "#000000")), mode_data),
        "accent-color": resolve_var(mode_data.get("accent-color",
                                    mode_data.get("m3-secondary", "#000000")), mode_data),
        "primary-background-color": resolve_var(mode_data.get("primary-background-color",
                                                mode_data.get("m3-surface", "#000000")), mode_data),
        "card-background-color": resolve_var(mode_data.get("card-background-color",
                                             mode_data.get("m3-surface-container", "#000000")), mode_data),
    }

themes = {}

for filename in os.listdir(themes_path):
    if not (filename.endswith(".yaml") or filename.endswith(".yml")):
        continue
    fullpath = os.path.join(themes_path, filename)
    try:
        with open(fullpath, "r") as f:
            data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                for theme_name, theme_values in data.items():
                    if not isinstance(theme_values, dict):
                        continue
                    
                    # Check if theme has modes (Material 3 structure)
                    if "modes" in theme_values and isinstance(theme_values["modes"], dict):
                        # Extract light and dark modes separately
                        theme_result = {"modes": {}}
                        
                        for mode in ["light", "dark"]:
                            if mode in theme_values["modes"]:
                                mode_data = theme_values["modes"][mode]
                                # Merge top-level values with mode-specific values for resolution
                                merged_data = {**theme_values, **mode_data}
                                theme_result["modes"][mode] = extract_colors_for_mode(merged_data)
                        
                        themes[theme_name] = theme_result
                    else:
                        # Legacy theme without modes - extract colors directly
                        themes[theme_name] = extract_colors_for_mode(theme_values)
                        
    except Exception as e:
        print(f"Error reading theme file {filename}: {e}")

with open(output_file, "w") as f:
    json.dump({"themes": themes}, f, indent=2)
    