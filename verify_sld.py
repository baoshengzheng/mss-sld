#!/usr/bin/env python3
"""
Verification suite for SLD generation:
1. Coverage check — every fclass in schema is covered in SLD
2. Style value check — spot-check against OSM Carto source .mss
3. XML well-formedness & SLD structure check
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).parent
SLD_DIR = BASE_DIR / "sld"

# Known z17 values extracted directly from OSM Carto .mss files
# (format: fclass → {property: expected_value})
EXPECTED_ROAD_VALUES = {
    "motorway":      {"casing_color": "#dc2a67", "casing_width": 18, "fill_color": "#e892a2", "fill_width": 12},
    "trunk":         {"casing_color": "#c84e2f", "casing_width": 18, "fill_color": "#f9b29c", "fill_width": 12},
    "primary":       {"casing_color": "#a06b00", "casing_width": 18, "fill_color": "#fcd6a4", "fill_width": 12},
    "secondary":     {"casing_color": "#707d05", "casing_width": 18, "fill_color": "#f7fabf", "fill_width": 12},
    "tertiary":      {"casing_color": "#8f8f8f", "casing_width": 18, "fill_color": "#ffffff", "fill_width": 12},
    "residential":   {"casing_color": "#bbbbbb", "casing_width": 12, "fill_color": "#ffffff", "fill_width": 7},
    "living_street": {"casing_color": "#bbbbbb", "casing_width": 12, "fill_color": "#ededed", "fill_width": 7},
    "pedestrian":    {"casing_color": "#999999", "casing_width": 12, "fill_color": "#dddde8", "fill_width": 7},
    "footway":       {"casing_color": "#ffffff", "casing_width": 1.3, "fill_color": "#fa8072", "fill_width": 0.9},
    "cycleway":      {"casing_color": "#ffffff", "casing_width": 0.9, "fill_color": "#0000ff", "fill_width": 0.6},
    "bridleway":     {"casing_color": "#ffffff", "casing_width": 1.2, "fill_color": "#008000", "fill_width": 0.8},
    "track":         {"casing_color": "#ffffff", "casing_width": 1.5, "fill_color": "#996600", "fill_width": 1.2},
    "service":       {"casing_color": "#bbbbbb", "casing_width": 7,  "fill_color": "#ffffff", "fill_width": 5},
}

EXPECTED_LANDUSE_VALUES = {
    "forest":       {"fill": "#add19e"},
    "park":         {"fill": "#c8facc"},
    "residential":  {"fill": "#e0dfdf"},
    "industrial":   {"fill": "#ebdbe8"},
    "commercial":   {"fill": "#f2dad9"},
    "retail":       {"fill": "#ffd6d1"},
    "farmland":     {"fill": "#eef0d5"},
    "cemetery":     {"fill": "#aacbaf"},
    "grass":        {"fill": "#cdebb0"},
    "meadow":       {"fill": "#cdebb0"},
    "quarry":       {"fill": "#c5c3c3"},
    "military":     {"fill": "#f55"},
    "scrub":        {"fill": "#c8d7ab"},
    "heath":        {"fill": "#d6d99f"},
}

EXPECTED_BUILDING_VALUES = {
    "buildings": {"fill": "#d9d0c9", "stroke": "#b0a7a0", "stroke-width": 0.75},
}

EXPECTED_WATER_VALUES = {
    "water":      {"fill": "#aad3df"},
    "reservoir":  {"fill": "#aad3df"},
    "river":      {"fill": "#aad3df"},
    "glacier":    {"fill": "#ddecec"},
}

# POI group colors (from amenity-points.mss)
EXPECTED_POI_COLORS = {
    "gastronomy":   "#C77400",   # @gastronomy-icon
    "accommodation": "#0092da",   # @accommodation-icon
    "health":        "#BF0000",   # @health-color
    "tourism":       "#734a08",   # @amenity-brown
    "shopping":      "#ac39ac",   # @shop-icon
    "sports":        "#0092da",   # mapped
    "public":        "#734a08",   # @public-service
    "man_made":      "#666666",   # @man-made-icon
    "culture":       "#734a08",   # @culture
    "education":     "#734a08",   # @amenity-brown
    "money":         "#734a08",   # @amenity-brown
}

NS = {
    'sld': 'http://www.opengis.net/sld',
    'ogc': 'http://www.opengis.net/ogc',
}

# ═══════════════════════════════════════════════════════════════
# Test 1: XML Well-formedness & SLD Structure
# ═══════════════════════════════════════════════════════════════

def check_xml_validity():
    """Verify all .sld files are well-formed XML with correct SLD structure."""
    print("=" * 60)
    print("TEST 1: XML Well-formedness & SLD Structure")
    print("=" * 60)
    errors = 0
    for f in sorted(SLD_DIR.glob("*.sld")):
        try:
            tree = ET.parse(f)
            root = tree.getroot()
            # Check root element
            if root.tag != '{http://www.opengis.net/sld}StyledLayerDescriptor':
                print(f"  FAIL {f.name}: wrong root element")
                errors += 1
                continue
            # Check at least one NamedLayer
            layers = root.findall('.//sld:NamedLayer', NS)
            if not layers:
                print(f"  FAIL {f.name}: no NamedLayer found")
                errors += 1
                continue
            # Check FeatureTypeStyle
            fts = root.findall('.//sld:FeatureTypeStyle', NS)
            if not fts:
                print(f"  FAIL {f.name}: no FeatureTypeStyle found")
                errors += 1
                continue
            # Check at least one Rule
            rules = root.findall('.//sld:Rule', NS)
            if not rules:
                print(f"  FAIL {f.name}: no Rules found")
                errors += 1
                continue
            # Check ScaleDenominator present in rules
            has_scale = any(r.find('sld:MinScaleDenominator', NS) is not None for r in rules)
            if not has_scale:
                print(f"  FAIL {f.name}: no ScaleDenominator in rules")
                errors += 1
                continue
            print(f"  OK  {f.name:45s}  {len(rules):3d} rules")
        except ET.ParseError as e:
            print(f"  FAIL {f.name}: XML parse error: {e}")
            errors += 1
    print(f"\nResult: {'ALL PASSED' if errors == 0 else f'{errors} FAILURES'}")
    return errors


# ═══════════════════════════════════════════════════════════════
# Test 2: Fclass Coverage
# ═══════════════════════════════════════════════════════════════

def parse_schema_fclasses():
    """Extract all fclass values from geofabrik_schema.yaml using a simple state parser."""
    schema = {}
    current_layer = None
    current_fclasses = []
    with open(BASE_DIR / "geofabrik_schema.yaml", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("  - name: "):
                if current_layer and current_fclasses:
                    schema[current_layer] = current_fclasses
                current_layer = line.split("name:")[1].strip()
                current_fclasses = []
            # Match lines like:  - { code: 1000, fclass: "city", ... }
            elif line.strip().startswith("- {") and "fclass:" in line and current_layer:
                # Extract the fclass value between fclass: and the next comma or "
                marker = 'fclass:'
                idx = line.index(marker) + len(marker)
                rest = line[idx:].strip().strip('"')
                # Take up to the closing quote
                end_quote = rest.find('"')
                if end_quote > 0:
                    val = rest[:end_quote]
                else:
                    # No quote, take until comma
                    val = rest.split(",")[0].strip().strip('"')
                current_fclasses.append(val)
        if current_layer and current_fclasses:
            schema[current_layer] = current_fclasses
    return schema


def parse_sld_fclasses(sld_file):
    """Extract all fclass values referenced in an SLD file."""
    tree = ET.parse(sld_file)
    root = tree.getroot()
    parent_map = {}
    for p in root.iter():
        for c in p:
            parent_map[c] = p

    fclasses = set()
    for literal in root.findall('.//ogc:Literal', NS):
        val = (literal.text or "").strip()
        if not val or val.startswith("#") or val.startswith("rgba") or val in ("", "name"):
            continue
        pe = parent_map.get(literal)
        if pe is not None:
            prop = pe.find('ogc:PropertyName', NS)
            if prop is not None and prop.text == 'fclass':
                fclasses.add(val)
    return fclasses


def check_coverage():
    """Verify every schema fclass has a matching rule in SLD."""
    print("\n" + "=" * 60)
    print("TEST 2: Fclass Coverage (schema → SLD)")
    print("=" * 60)

    schema = parse_schema_fclasses()
    all_errors = 0

    # Map Geofabrik layer names to SLD file patterns
    layer_to_sld = {
        "places":           ["gis_osm_places_free_1.sld", "gis_osm_places_a_free_1.sld"],
        "pois":             ["gis_osm_pois_free_1.sld", "gis_osm_pois_a_free_1.sld"],
        "pofw":             ["gis_osm_pofw_free_1.sld", "gis_osm_pofw_a_free_1.sld"],
        "natural":          ["gis_osm_natural_free_1.sld", "gis_osm_natural_a_free_1.sld"],
        "traffic":          ["gis_osm_traffic_free_1.sld", "gis_osm_traffic_a_free_1.sld"],
        "transport":        ["gis_osm_transport_free_1.sld", "gis_osm_transport_a_free_1.sld"],
        "roads":            ["gis_osm_roads_free_1.sld"],
        "railways":         ["gis_osm_railways_free_1.sld"],
        "waterways":        ["gis_osm_waterways_free_1.sld"],
        "adminareas":       ["gis_osm_adminareas_a_free_1.sld"],
        "buildings":        ["gis_osm_buildings_a_free_1.sld"],
        "landuse":          ["gis_osm_landuse_a_free_1.sld"],
        "protected_areas":  ["gis_osm_protected_areas_a_free_1.sld"],
        "water":            ["gis_osm_water_a_free_1.sld"],
    }

    for layer_name, sld_files in layer_to_sld.items():
        if layer_name not in schema:
            print(f"  SKIP {layer_name}: not in schema")
            continue

        schema_fclasses = set(schema[layer_name])
        sld_fclasses = set()
        for sf in sld_files:
            fp = SLD_DIR / sf
            if fp.exists():
                sld_fclasses |= parse_sld_fclasses(fp)

        missing = schema_fclasses - sld_fclasses
        extra = sld_fclasses - schema_fclasses

        if missing:
            print(f"  WARN {layer_name}: MISSING fclasses in SLD: {sorted(missing)}")
            all_errors += len(missing)
        else:
            print(f"  OK  {layer_name:20s}  {len(schema_fclasses):3d} schema fclasses → {len(sld_fclasses):3d} in SLD  (all covered)")

    print(f"\nResult: {'ALL COVERED' if all_errors == 0 else f'{all_errors} MISSING fclass values'}")
    return all_errors


# ═══════════════════════════════════════════════════════════════
# Test 3: Style Value Correctness
# ═══════════════════════════════════════════════════════════════

def get_sld_rule_params(sld_file):
    """Parse SLD and return dict of {rule_name: {param: value}}."""
    tree = ET.parse(sld_file)
    root = tree.getroot()
    rules = {}

    # Build a parent map since stdlib ElementTree lacks getparent()
    parent_map = {}
    for p in root.iter():
        for c in p:
            parent_map[c] = p

    for rule in root.findall('.//sld:Rule', NS):
        name_el = rule.find('sld:Name', NS)
        if name_el is None:
            continue
        rule_name = name_el.text
        params = {}

        # Get fclass from OGC Filter
        for lit in rule.findall('.//ogc:Literal', NS):
            val = (lit.text or "").strip()
            pe = parent_map.get(lit)
            if pe is not None:
                prop = pe.find('ogc:PropertyName', NS)
                if prop is not None and prop.text == 'fclass':
                    params['fclass'] = val

        # Get symbolizer params
        for css in rule.findall('.//sld:CssParameter', NS):
            pname = css.get('name', '')
            pval = css.text or ""
            params[pname] = pval

        rules[rule_name] = params
    return rules


def check_road_values():
    """Spot-check road SLD values against expected OSM Carto values."""
    print("\n" + "=" * 60)
    print("TEST 3: Road Style Value Correctness")
    print("=" * 60)
    errors = 0
    rules = get_sld_rule_params(SLD_DIR / "gis_osm_roads_free_1.sld")

    for fclass, expected in EXPECTED_ROAD_VALUES.items():
        casing_name = f"road_{fclass}_casing"
        fill_name = f"road_{fclass}_fill"

        if casing_name not in rules:
            print(f"  FAIL {casing_name}: rule not found")
            errors += 1
            continue
        if fill_name not in rules:
            print(f"  FAIL {fill_name}: rule not found")
            errors += 1
            continue

        casing = rules[casing_name]
        fill = rules[fill_name]

        # Check casing color
        if casing.get('stroke') != expected['casing_color']:
            print(f"  FAIL {fclass} casing color: got {casing.get('stroke')}, expected {expected['casing_color']}")
            errors += 1
        # Check casing width
        got_cw = float(casing.get('stroke-width', 0))
        if abs(got_cw - expected['casing_width']) > 0.05:
            print(f"  FAIL {fclass} casing width: got {got_cw}, expected {expected['casing_width']}")
            errors += 1
        # Check fill color
        if fill.get('stroke') != expected['fill_color']:
            print(f"  FAIL {fclass} fill color: got {fill.get('stroke')}, expected {expected['fill_color']}")
            errors += 1
        # Check fill width
        got_fw = float(fill.get('stroke-width', 0))
        if abs(got_fw - expected['fill_width']) > 0.05:
            print(f"  FAIL {fclass} fill width: got {got_fw}, expected {expected['fill_width']}")
            errors += 1

        print(f"  OK  {fclass:20s} casing={expected['casing_color']}/{expected['casing_width']}px  fill={expected['fill_color']}/{expected['fill_width']}px")

    print(f"\nResult: {'ALL CORRECT' if errors == 0 else f'{errors} MISMATCHES'}")
    return errors


def check_landuse_values():
    """Spot-check landuse SLD values."""
    print("\n" + "=" * 60)
    print("TEST 4: Landuse Style Value Correctness")
    print("=" * 60)
    errors = 0
    rules = get_sld_rule_params(SLD_DIR / "gis_osm_landuse_a_free_1.sld")

    for fclass, expected in EXPECTED_LANDUSE_VALUES.items():
        rule_name = f"landuse_{fclass}"
        if rule_name not in rules:
            print(f"  FAIL {rule_name}: rule not found")
            errors += 1
            continue
        got_fill = rules[rule_name].get('fill', '')
        if got_fill != expected['fill']:
            print(f"  FAIL {fclass}: got {got_fill}, expected {expected['fill']}")
            errors += 1
        else:
            print(f"  OK  {fclass:20s} fill={expected['fill']}")

    print(f"\nResult: {'ALL CORRECT' if errors == 0 else f'{errors} MISMATCHES'}")
    return errors


def check_building_values():
    """Spot-check building SLD values."""
    print("\n" + "=" * 60)
    print("TEST 5: Building Style Value Correctness")
    print("=" * 60)
    errors = 0
    rules = get_sld_rule_params(SLD_DIR / "gis_osm_buildings_a_free_1.sld")

    for fclass, expected in EXPECTED_BUILDING_VALUES.items():
        rule_name = "building_fill"
        if rule_name not in rules:
            print(f"  FAIL {rule_name}: rule not found")
            errors += 1
            continue
        r = rules[rule_name]
        for key, exp_val in expected.items():
            got = r.get(key, '')
            try:
                got_f = float(got)
                if abs(got_f - float(exp_val)) > 0.01:
                    print(f"  FAIL {fclass} {key}: got {got}, expected {exp_val}")
                    errors += 1
            except ValueError:
                if got != exp_val:
                    print(f"  FAIL {fclass} {key}: got {got}, expected {exp_val}")
                    errors += 1
        print(f"  OK  buildings: fill={expected['fill']} stroke={expected['stroke']} width={expected['stroke-width']}")

    print(f"\nResult: {'ALL CORRECT' if errors == 0 else f'{errors} MISMATCHES'}")
    return errors


def check_water_values():
    """Spot-check water SLD values."""
    print("\n" + "=" * 60)
    print("TEST 6: Water Style Value Correctness")
    print("=" * 60)
    errors = 0
    rules = get_sld_rule_params(SLD_DIR / "gis_osm_water_a_free_1.sld")

    for fclass, expected in EXPECTED_WATER_VALUES.items():
        # The water rule uses OR filter, check the water_body rule
        rule_name = "water_body" if fclass in ("water", "reservoir", "river") else f"water_{fclass}"
        if rule_name not in rules:
            print(f"  FAIL {rule_name}: rule not found")
            errors += 1
            continue
        got_fill = rules[rule_name].get('fill', '')
        if got_fill != expected['fill']:
            print(f"  FAIL {fclass}: got {got_fill}, expected {expected['fill']}")
            errors += 1
        else:
            print(f"  OK  {fclass:20s} fill={expected['fill']}")

    print(f"\nResult: {'ALL CORRECT' if errors == 0 else f'{errors} MISMATCHES'}")
    return errors


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    total_errors = 0
    total_errors += check_xml_validity()
    total_errors += check_coverage()
    total_errors += check_road_values()
    total_errors += check_landuse_values()
    total_errors += check_building_values()
    total_errors += check_water_values()

    print("\n" + "=" * 60)
    print(f"VERIFICATION COMPLETE: {'ALL PASSED' if total_errors == 0 else f'{total_errors} TOTAL ISSUES FOUND'}")
    print("=" * 60)
    sys.exit(1 if total_errors > 0 else 0)
