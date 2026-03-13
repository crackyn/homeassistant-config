"""
Generate subview YAML files for each Floor → Area combination.
Run once, then delete this script if desired.
"""
import os

VIEWS_DIR = os.path.join(os.path.dirname(__file__), "..", "ui-lovelace", "dashboards", "home", "views")

CARD_MOD_BADGE = """\
    card_mod:
      style: |
        :host {
          --label-badge-background-color: var(--m3-surface-container, var(--card-background-color));
          --label-badge-text-color: var(--m3-on-surface, var(--primary-text-color));
        }"""

def badge(entity_id: str) -> str:
    return f"""\
  - type: entity
    show_name: false
    show_state: true
    show_icon: true
    entity: {entity_id}
{CARD_MOD_BADGE}"""

def badges_for_area(area_id: str) -> str:
    entities = [
        f"sensor.{area_id}_average_temperature",
        f"sensor.{area_id}_average_humidity",
        f"binary_sensor.motion_{area_id}",
        f"binary_sensor.occupancy_{area_id}",
    ]
    return "\n".join(badge(e) for e in entities)

def section(area_id: str, domain: str, group_name: str, group_icon: str) -> str:
    return f"""\
  - type: grid
    cards:
      - type: custom:streamline-card
        template: section_2col_card
        variables:
          area_id: {area_id}
          domain: {domain}
          group_name: {group_name}
          group_icon: {group_icon}"""

def sections_for_area(area_id: str) -> str:
    items = [
        (area_id, "light",        "Lights",   "mdi:lightbulb=group"),
        (area_id, "fan",          "Fans",     "mdi:fan"),
        (area_id, "media_player", "Media",    "mdi:television-play"),
        (area_id, "switch",       "Switches", "mdi:light-switch"),
    ]
    return "\n".join(section(*i) for i in items)

def single_area_view(floor_slug: str, area_id: str, title: str, icon: str) -> str:
    path = f"{floor_slug}-{area_id.replace('_', '-')}"
    return f"""\
type: sections
max_columns: 3
path: {path}
title: {title}
icon: {icon}
show_icon_and_title: true
subview: true
dense_section_placement: true
cards: []
badges:
{badges_for_area(area_id)}
sections:
{sections_for_area(area_id)}
"""

def combined_view(path: str, title: str, icon: str, areas: list[tuple[str, str]]) -> str:
    """areas = list of (area_id, display_name)"""
    all_badges = "\n".join(badges_for_area(a_id) for a_id, _ in areas)
    all_sections_parts = []
    for area_id, display_name in areas:
        items = [
            (area_id, "light",        f"{display_name} Lights",   "mdi:lightbulb=group"),
            (area_id, "fan",          f"{display_name} Fans",     "mdi:fan"),
            (area_id, "media_player", f"{display_name} Media",    "mdi:television-play"),
            (area_id, "switch",       f"{display_name} Switches", "mdi:light-switch"),
        ]
        all_sections_parts.append("\n".join(section(*i) for i in items))
    all_sections = "\n".join(all_sections_parts)
    return f"""\
type: sections
max_columns: 3
path: {path}
title: {title}
icon: {icon}
show_icon_and_title: true
subview: true
dense_section_placement: true
cards: []
badges:
{all_badges}
sections:
{all_sections}
"""

# ── Area definitions ────────────────────────────────────────────────────────
# (floor_slug, area_id, display_title, icon)

INDIVIDUAL_AREAS = [
    # Main Floor (living_room and dining_room already exist — skip)
    ("main-floor", "kitchen",            "Kitchen",                   "hue:room-kitchen"),
    ("main-floor", "laundry_room",       "Laundry Room",              "mdi:washing-machine"),
    ("main-floor", "master_bedroom",     "Master Bedroom",            "hue:room-bedroom"),
    ("main-floor", "master_bathroom",    "Master Bathroom",           "hue:room-bathroom"),
    ("main-floor", "garage",             "Garage",                    "mdi:garage"),
    ("main-floor", "garage_storage",     "Garage Storage",            "mdi:garage-lock"),
    ("main-floor", "hallway_bathroom",   "Hallway Bathroom",          "hue:room-bathroom"),
    # Basement
    ("basement",   "basement",           "Basement",                  "mdi:home-floor-negative-1"),
    ("basement",   "gym",                "Gym",                       "mdi:dumbbell"),
    ("basement",   "storage",            "Storage",                   "mdi:package-variant"),
    # Upstairs
    ("upstairs",   "bedroom",            "Bedroom",                   "hue:room-bedroom"),
    ("upstairs",   "office",             "Office",                    "hue:room-office"),
    ("upstairs",   "upstairs_hallway_bathroom", "Upstairs Hallway Bathroom", "hue:room-bathroom"),
    ("upstairs",   "upstairs_hallway_closet",   "Upstairs Hallway Closet",   "mdi:wardrobe"),
    ("upstairs",   "office_closet",      "Office Closet",             "mdi:wardrobe"),
    ("upstairs",   "bedroom_closet",     "Bedroom Closet",            "mdi:wardrobe"),
    # Outside
    ("outside",    "front_yard",         "Front Yard",                "mdi:flower"),
    ("outside",    "back_yard",          "Back Yard",                 "mdi:grill"),
    ("outside",    "gazebo",             "Gazebo",                    "mdi:pergola"),
    ("outside",    "outside",            "Outside",                   "mdi:weather-sunny"),
]

COMBINED_VIEWS = [
    # (path, title, icon, [(area_id, display_name), ...])
    ("home", "Home", "mdi:home", [
        ("upstairs_hallway",  "Upstairs Hallway"),
        ("hallway",           "Hallway"),
        ("stairs",            "Stairs"),
        ("basement_stairs",   "Basement Stairs"),
    ]),
    ("system", "System", "mdi:cog", [
        ("home",       "Home"),
        ("unassigned", "Unassigned"),
    ]),
]

def main():
    os.makedirs(VIEWS_DIR, exist_ok=True)
    created = []

    for floor_slug, area_id, title, icon in INDIVIDUAL_AREAS:
        filename = f"sv_{floor_slug.replace('-', '_')}_{area_id}.yaml"
        filepath = os.path.join(VIEWS_DIR, filename)
        content = single_area_view(floor_slug, area_id, title, icon)
        with open(filepath, "w", newline="\n") as f:
            f.write(content)
        created.append(filename)

    for path, title, icon, areas in COMBINED_VIEWS:
        filename = f"sv_{path}.yaml"
        filepath = os.path.join(VIEWS_DIR, filename)
        content = combined_view(path, title, icon, areas)
        with open(filepath, "w", newline="\n") as f:
            f.write(content)
        created.append(filename)

    print(f"Created {len(created)} subview files:")
    for f in sorted(created):
        print(f"  {f}")

if __name__ == "__main__":
    main()
