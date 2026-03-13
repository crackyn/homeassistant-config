#!/usr/bin/env python3
"""
Split Flattened Dashboard Script

Reads the flattened dashboard.yaml and splits it back into:
- Individual view files in the views/ directory
- Individual button_card_templates in ../../templates/button-cards/

This allows editing the flattened dashboard and then regenerating the split files.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any
import yaml
from collections import OrderedDict


class MySafeDumper(yaml.SafeDumper):
    """Custom YAML dumper with specific formatting."""
    def increase_indent(self, flow=False, indentless=False):
        return super(MySafeDumper, self).increase_indent(flow, False)


def represent_none(self, _):
    """Represent None as empty string instead of 'null'."""
    return self.represent_scalar('tag:yaml.org,2002:null', '')


MySafeDumper.add_representer(type(None), represent_none)


def ordered_dict_representer(dumper, data):
    """Preserve order of dictionaries."""
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.add_representer(OrderedDict, ordered_dict_representer, Dumper=MySafeDumper)


class LiteralString(str):
    """String type that will be dumped as literal (|) style."""
    pass


def literal_string_representer(dumper, data):
    """Represent literal strings with | style."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(LiteralString, literal_string_representer, Dumper=MySafeDumper)


def get_view_filename(view: Dict[str, Any], index: int) -> str:
    """
    Generate a filename for a view based on its properties.
    
    Args:
        view: The view dictionary
        index: The index of the view in the views list
        
    Returns:
        Filename for the view
    """
    # Get the path to use as base name
    path = view.get('path', '')
    
    # Special handling for index 0 (main home view)
    if index == 0:
        return '00_home.yaml'
    
    # Handle floor navigation views (non-subviews that have floor- prefix)
    if path.startswith('floor-'):
        # Extract the suffix after 'floor-'
        suffix = path[6:]  # Remove 'floor-' prefix
        
        if suffix == 'main-floor':
            return '10_main_floor.yaml'
        elif suffix == 'upstairs':
            return '20_upstairs.yaml'
        elif suffix == 'basement':
            return '30_basement.yaml'
        elif suffix == 'home-areas':
            return '40_home.yaml'
        elif suffix == 'system-areas':
            return '50_system.yaml'
        elif suffix == 'outside':
            return '60_outside.yaml'
        else:
            # Unknown floor type, use generic naming
            clean_suffix = suffix.replace('-', '_')
            return f'{index * 10:02d}_{clean_suffix}.yaml'
    
    # Handle subviews
    if path.startswith('main-floor-'):
        suffix = path[11:]  # Remove 'main-floor-' prefix
        clean_suffix = suffix.replace('-', '_')
        return f'10_sv_main_floor_{clean_suffix}.yaml'
    
    elif path.startswith('upstairs-'):
        suffix = path[9:]  # Remove 'upstairs-' prefix
        clean_suffix = suffix.replace('-', '_')
        return f'20_sv_upstairs_{clean_suffix}.yaml'
    
    elif path.startswith('basement-'):
        suffix = path[9:]  # Remove 'basement-' prefix
        clean_suffix = suffix.replace('-', '_')
        return f'30_sv_basement_{clean_suffix}.yaml'
    
    elif path == 'home':
        return '40_sv_home.yaml'
    
    elif path == 'system':
        return '50_sv_system.yaml'
    
    elif path.startswith('outside-'):
        suffix = path[8:]  # Remove 'outside-' prefix
        clean_suffix = suffix.replace('-', '_')
        return f'60_sv_outside_{clean_suffix}.yaml'
    
    # Default fallback for unknown patterns
    clean_path = path.replace('-', '_') if path else f'view_{index}'
    return f'{index * 10:02d}_{clean_path}.yaml'


def split_dashboard(
    flattened_path: str,
    views_dir: str,
    templates_dir: str,
    dry_run: bool = False
) -> None:
    """
    Split the flattened dashboard into individual files.
    
    Args:
        flattened_path: Path to the flattened dashboard.yaml
        views_dir: Directory where view files should be written
        templates_dir: Directory where button card template files should be written
        dry_run: If True, don't write files, just print what would be done
    """
    print(f"Reading flattened dashboard from: {flattened_path}")
    
    # Read the flattened dashboard
    with open(flattened_path, 'r', encoding='utf-8') as f:
        dashboard = yaml.safe_load(f)
    
    if not dashboard:
        print("ERROR: Could not load dashboard YAML")
        return
    
    # Extract and split button_card_templates
    if 'button_card_templates' in dashboard:
        templates = dashboard['button_card_templates']
        print(f"\nFound {len(templates)} button card templates")
        
        # Create templates directory if it doesn't exist
        if not dry_run:
            os.makedirs(templates_dir, exist_ok=True)
        
        # Get existing template files to track what to remove
        existing_templates = set()
        if os.path.exists(templates_dir):
            existing_templates = {
                f for f in os.listdir(templates_dir)
                if f.endswith('.yaml') and f != 'dummy.txt'
            }
        
        new_templates = set()
        
        for template_name, template_content in templates.items():
            filename = f"{template_name}.yaml"
            new_templates.add(filename)
            filepath = os.path.join(templates_dir, filename)
            
            # Create the template file with the template name as the top-level key
            template_data = {template_name: template_content}
            
            if dry_run:
                print(f"  Would write: {filepath}")
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Write YAML document separator
                    f.write('---\n')
                    yaml.dump(
                        template_data,
                        f,
                        Dumper=MySafeDumper,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                        width=120
                    )
                print(f"  ✓ Wrote: {filepath}")
        
        # Remove templates that no longer exist
        templates_to_remove = existing_templates - new_templates
        for template_file in templates_to_remove:
            filepath = os.path.join(templates_dir, template_file)
            if dry_run:
                print(f"  Would remove: {filepath}")
            else:
                os.remove(filepath)
                print(f"  ✗ Removed: {filepath}")
    
    # Extract and split views
    if 'views' in dashboard:
        views = dashboard['views']
        print(f"\nFound {len(views)} views")
        
        # Create views directory if it doesn't exist
        if not dry_run:
            os.makedirs(views_dir, exist_ok=True)
        
        # Get existing view files to track what to remove
        existing_views = set()
        if os.path.exists(views_dir):
            existing_views = {
                f for f in os.listdir(views_dir)
                if f.endswith('.yaml') and f != 'dummy.txt'
            }
        
        new_views = set()
        
        for index, view in enumerate(views):
            filename = get_view_filename(view, index)
            new_views.add(filename)
            filepath = os.path.join(views_dir, filename)
            
            if dry_run:
                print(f"  Would write: {filepath}")
                print(f"    Title: {view.get('title', 'N/A')}")
                print(f"    Path: {view.get('path', 'N/A')}")
            else:
                # Write the view as a single YAML document (not wrapped in 'views:')
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(
                        view,
                        f,
                        Dumper=MySafeDumper,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                        width=120
                    )
                print(f"  ✓ Wrote: {filepath}")
                print(f"    Title: {view.get('title', 'N/A')}")
                print(f"    Path: {view.get('path', 'N/A')}")
        
        # Remove views that no longer exist
        views_to_remove = existing_views - new_views
        for view_file in views_to_remove:
            filepath = os.path.join(views_dir, view_file)
            if dry_run:
                print(f"  Would remove: {filepath}")
            else:
                os.remove(filepath)
                print(f"  ✗ Removed: {filepath}")
    
    print("\n✓ Split complete!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Split flattened dashboard into individual view and template files'
    )
    parser.add_argument(
        '--flattened',
        default=None,
        help='Path to flattened dashboard.yaml (default: ../flattened/dashboard.yaml)'
    )
    parser.add_argument(
        '--views-dir',
        default=None,
        help='Directory for view files (default: ../views)'
    )
    parser.add_argument(
        '--templates-dir',
        default=None,
        help='Directory for button card templates (default: ../../../templates/button-cards)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    # Determine script directory
    script_dir = Path(__file__).parent.absolute()
    
    # Set default paths relative to script location
    flattened_path = args.flattened or str(script_dir / '..' / 'flattened' / 'dashboard.yaml')
    views_dir = args.views_dir or str(script_dir / '..' / 'views')
    templates_dir = args.templates_dir or str(script_dir / '..' / '..' / '..' / 'templates' / 'button-cards')
    
    # Resolve to absolute paths
    flattened_path = str(Path(flattened_path).resolve())
    views_dir = str(Path(views_dir).resolve())
    templates_dir = str(Path(templates_dir).resolve())
    
    if not os.path.exists(flattened_path):
        print(f"ERROR: Flattened dashboard not found: {flattened_path}")
        sys.exit(1)
    
    split_dashboard(flattened_path, views_dir, templates_dir, args.dry_run)


if __name__ == '__main__':
    main()
