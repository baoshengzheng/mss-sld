#!/usr/bin/env python3
"""
SLD 1.0 Generator: Geofabrik OSM Schema → OSM Carto z17 styles
Generates SLD XML files matching Geofabrik Shapefile naming convention.

Filenames follow the pattern:
    gis_osm_<layer>_free_1.sld    — point/line geometry
    gis_osm_<layer>_a_free_1.sld  — area (polygon) geometry

Usage:
    python generate_sld.py              # Generate all SLD files
    python generate_sld.py --layer roads  # Generate single layer

Scale: z17 (ScaleDenominator ~2500–5000 at 90 DPI, EPSG:4326)
"""

import os
import sys
import argparse

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sld")

# ScaleDenominator for z17 at 90 DPI, WGS84
# z17 ground resolution ≈ 1.19 m/pixel, SD = 1.19 / 0.00028 ≈ 4250
Z17_MIN_SCALE_DENOM = 2500
Z17_MAX_SCALE_DENOM = 5000

SLD_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor
    xmlns:sld="http://www.opengis.net/sld"
    xmlns="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:gml="http://www.opengis.net/gml">
'''

SLD_FOOTER = '</sld:StyledLayerDescriptor>\n'


def esc(s):
    """Escape XML special characters."""
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ═══════════════════════════════════════════════════════════════
# FILTER HELPERS
# ═══════════════════════════════════════════════════════════════

def ogc_filter_property(property_name, value):
    return f'''
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>{property_name}</ogc:PropertyName>
              <ogc:Literal>{esc(value)}</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>'''


def ogc_or(prop_name, values):
    """OGC OR filter for multiple values on same property."""
    if len(values) == 1:
        return ogc_filter_property(prop_name, values[0])
    items = ""
    for v in values:
        items += f'''
              <ogc:PropertyIsEqualTo>
                <ogc:PropertyName>{prop_name}</ogc:PropertyName>
                <ogc:Literal>{esc(v)}</ogc:Literal>
              </ogc:PropertyIsEqualTo>'''
    return f'''
          <ogc:Filter>
            <ogc:Or>{items}
            </ogc:Or>
          </ogc:Filter>'''


def ogc_and(*filters):
    """Combine filters with AND."""
    inner = "".join(filters)
    return f'''
          <ogc:Filter>
            <ogc:And>{inner}
            </ogc:And>
          </ogc:Filter>'''


# ═══════════════════════════════════════════════════════════════
# SYMBOLIZER BUILDERS
# ═══════════════════════════════════════════════════════════════

def scale(mn=Z17_MIN_SCALE_DENOM, mx=Z17_MAX_SCALE_DENOM):
    return f'''
          <sld:MinScaleDenominator>{mn}</sld:MinScaleDenominator>
          <sld:MaxScaleDenominator>{mx}</sld:MaxScaleDenominator>'''


def polygon_sym(fill, stroke=None, sw=None, dash=None, opacity=None):
    """PolygonSymbolizer."""
    # "none" means no fill — omit the Fill element entirely
    if fill and fill != "none":
        f = f'''
            <sld:Fill>
              <sld:CssParameter name="fill">{fill}</sld:CssParameter>'''
        if opacity:
            f += f'''
              <sld:CssParameter name="fill-opacity">{opacity}</sld:CssParameter>'''
        f += '''
            </sld:Fill>'''
    else:
        f = ""

    s = ""
    if stroke and stroke != "none":
        s = f'''
            <sld:Stroke>
              <sld:CssParameter name="stroke">{stroke}</sld:CssParameter>
              <sld:CssParameter name="stroke-width">{sw or 0.5}</sld:CssParameter>'''
        if dash:
            parts = dash.split(",")
            if len(parts) == 2:
                s += f'''
              <sld:CssParameter name="stroke-dasharray">{parts[0].strip()} {parts[1].strip()}</sld:CssParameter>'''
        s += '''
            </sld:Stroke>'''

    return f'''
          <sld:PolygonSymbolizer>{f}{s}
          </sld:PolygonSymbolizer>'''


def line_sym(stroke, width, dash=None, cap=None, join="round"):
    """LineSymbolizer."""
    x = f'''
          <sld:LineSymbolizer>
            <sld:Stroke>
              <sld:CssParameter name="stroke">{stroke}</sld:CssParameter>
              <sld:CssParameter name="stroke-width">{width}</sld:CssParameter>'''
    if dash:
        parts = str(dash).split(",")
        if len(parts) == 2:
            x += f'''
              <sld:CssParameter name="stroke-dasharray">{parts[0].strip()} {parts[1].strip()}</sld:CssParameter>'''
    if cap:
        x += f'''
              <sld:CssParameter name="stroke-linecap">{cap}</sld:CssParameter>'''
    if join:
        x += f'''
              <sld:CssParameter name="stroke-linejoin">{join}</sld:CssParameter>'''
    x += '''
            </sld:Stroke>
          </sld:LineSymbolizer>'''
    return x


def point_sym(fill, size=6, stroke_color=None, stroke_width=1, shape="circle"):
    """PointSymbolizer."""
    st = ""
    if stroke_color:
        st = f'''
              <sld:Stroke>
                <sld:CssParameter name="stroke">{stroke_color}</sld:CssParameter>
                <sld:CssParameter name="stroke-width">{stroke_width}</sld:CssParameter>
              </sld:Stroke>'''
    return f'''
          <sld:PointSymbolizer>
            <sld:Graphic>
              <sld:Mark>
                <sld:WellKnownName>{shape}</sld:WellKnownName>
                <sld:Fill>
                  <sld:CssParameter name="fill">{fill}</sld:CssParameter>
                </sld:Fill>{st}
              </sld:Mark>
              <sld:Size>{size}</sld:Size>
            </sld:Graphic>
          </sld:PointSymbolizer>'''


def text_sym(label_field="name", font="Noto Sans, Arial, sans-serif", size=10,
              fill="#222222", halo_fill="rgba(255,255,255,0.6)", halo_radius=1,
              placement="point"):
    """TextSymbolizer."""
    if placement == "line":
        place_xml = '''
            <sld:LabelPlacement>
              <sld:LinePlacement>
                <sld:PerpendicularOffset>0</sld:PerpendicularOffset>
              </sld:LinePlacement>
            </sld:LabelPlacement>'''
    else:
        place_xml = '''
            <sld:LabelPlacement>
              <sld:PointPlacement>
                <sld:AnchorPoint>
                  <sld:AnchorX>0.5</sld:AnchorX>
                  <sld:AnchorY>0.5</sld:AnchorY>
                </sld:AnchorPoint>
                <sld:Displacement>
                  <sld:DisplacementX>0</sld:DisplacementX>
                  <sld:DisplacementY>-10</sld:DisplacementY>
                </sld:Displacement>
              </sld:PointPlacement>
            </sld:LabelPlacement>'''

    return f'''
          <sld:TextSymbolizer>
            <sld:Label>
              <ogc:PropertyName>{label_field}</ogc:PropertyName>
            </sld:Label>
            <sld:Font>
              <sld:CssParameter name="font-family">{font}</sld:CssParameter>
              <sld:CssParameter name="font-size">{size}</sld:CssParameter>
              <sld:CssParameter name="font-style">normal</sld:CssParameter>
              <sld:CssParameter name="font-weight">normal</sld:CssParameter>
            </sld:Font>{place_xml}
            <sld:Fill>
              <sld:CssParameter name="fill">{fill}</sld:CssParameter>
            </sld:Fill>
            <sld:Halo>
              <sld:Radius>{halo_radius}</sld:Radius>
              <sld:Fill>
                <sld:CssParameter name="fill">{halo_fill}</sld:CssParameter>
              </sld:Fill>
            </sld:Halo>
          </sld:TextSymbolizer>'''


# ═══════════════════════════════════════════════════════════════
# STRUCTURE BUILDERS
# ═══════════════════════════════════════════════════════════════

def rule(name, filter_str, scale_str, sym_list):
    """Build a Rule element."""
    if isinstance(sym_list, str):
        sym_list = [sym_list]
    syms = "\n".join(sym_list)
    return f'''
        <sld:Rule>
          <sld:Name>{name}</sld:Name>{filter_str}{scale_str}{syms}
        </sld:Rule>'''


def named_layer(layer_geom_name, title, rules_xml):
    """Build NamedLayer → UserStyle → FeatureTypeStyle."""
    return f'''
  <sld:NamedLayer>
    <sld:Name>{layer_geom_name}</sld:Name>
    <sld:UserStyle>
      <sld:Name>{layer_geom_name}_style</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Name>{layer_geom_name}_fts</sld:Name>{rules_xml}
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>'''


# ═══════════════════════════════════════════════════════════════
# LAYER GENERATORS
# ═══════════════════════════════════════════════════════════════

def gen_landuse_a():
    """gis_osm_landuse_a_free_1.sld — Polygon"""
    items = [
        ("forest",            "#add19e", None, None),
        ("park",              "#c8facc", None, None),
        ("residential",       "#e0dfdf", "#b9b9b9", 0.5),
        ("industrial",        "#ebdbe8", "#c6b3c3", 0.5),
        ("commercial",        "#f2dad9", "#d1b2b0", 0.5),
        ("retail",            "#ffd6d1", "#d99c95", 0.5),
        ("farmland",          "#eef0d5", "#c7c9ae", 0.5),
        ("farmyard",          "#f5dcba", "#d1b48c", 0.5),
        ("meadow",            "#cdebb0", None, None),
        ("grass",             "#cdebb0", None, None),
        ("allotments",        "#c9e1bf", None, None),
        ("cemetery",          "#aacbaf", None, None),
        ("recreation_ground", "#c8facc", None, None),
        ("orchard",           "#aedfa3", None, None),
        ("vineyard",          "#aedfa3", None, None),
        ("scrub",             "#c8d7ab", None, None),
        ("heath",             "#d6d99f", None, None),
        ("quarry",            "#c5c3c3", None, None),
        ("landfill",          "#e0dfdf", "#c0c0c0", 0.5),
    ]
    # Military has special hatching (approximated with red fill + low opacity)
    items.append(("military", "#f55", None, None))

    r = ""
    for fclass, fill, stroke, sw in items:
        r += rule(f"landuse_{fclass}",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  polygon_sym(fill, stroke, sw))
    return named_layer("gis_osm_landuse_a_free_1", "Land Use (Area) - OSM Carto z17", r)


def gen_buildings_a():
    """gis_osm_buildings_a_free_1.sld — Polygon"""
    r = ""
    r += rule("building_fill",
              ogc_or("fclass", ["buildings"]),
              scale(Z17_MIN_SCALE_DENOM, Z17_MAX_SCALE_DENOM),
              polygon_sym("#d9d0c9", "#b0a7a0", 0.75))
    return named_layer("gis_osm_buildings_a_free_1", "Buildings (Area) - OSM Carto z17", r)


def gen_water_a():
    """gis_osm_water_a_free_1.sld — Polygon"""
    r = ""
    # Regular water bodies
    r += rule("water_body",
              ogc_or("fclass", ["water", "reservoir", "river", "dock"]),
              scale(),
              polygon_sym("#aad3df"))
    # Glacier
    r += rule("water_glacier",
              ogc_or("fclass", ["glacier"]),
              scale(),
              polygon_sym("#ddecec", "#9cf", 1.5, "4,2"))
    # Wetland
    r += rule("water_wetland",
              ogc_or("fclass", ["wetland"]),
              scale(),
              polygon_sym("#b5d0d0", None, None, None, 0.5))
    # Text labels on water
    r += rule("water_label",
              ogc_or("fclass", ["water", "reservoir", "river"]),
              scale(),
              text_sym("name", "Noto Sans Italic, Arial Italic, sans-serif", 10,
                        "#4d80b3", "rgba(255,255,255,0.6)", 1))
    return named_layer("gis_osm_water_a_free_1", "Water Bodies (Area) - OSM Carto z17", r)


def gen_waterways():
    """gis_osm_waterways_free_1.sld — Line"""
    r = ""
    ww = [("river", "#aad3df", 10, None),
          ("stream", "#aad3df", 3.5, None),
          ("canal", "#aad3df", 14, None),
          ("drain", "#aad3df", 3, None)]
    for fclass, color, width, dash in ww:
        r += rule(f"waterway_{fclass}",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  line_sym(color, width, dash, cap="round"))
    # River labels
    r += rule("waterway_river_label",
              ogc_or("fclass", ["river"]),
              scale(),
              text_sym("name", "Noto Sans Italic, Arial Italic, sans-serif", 10,
                        "#4d80b3", "rgba(255,255,255,0.6)", 1, "line"))
    return named_layer("gis_osm_waterways_free_1", "Waterways (Line) - OSM Carto z17", r)


def gen_transport():
    """gis_osm_transport_free_1.sld — Point"""
    r = ""
    items = [
        (["railway_station", "railway_halt"], "#0092da", 8),
        (["tram_stop"], "#0092da", 6),
        (["bus_stop"], "#0092da", 6),
        (["bus_station"], "#0092da", 8),
        (["taxi_rank"], "#0092da", 6),
        (["airport", "airfield", "helipad", "apron"], "#8461C4", 8),
        (["ferry_terminal"], "#8461C4", 8),
        (["aerialway_station"], "#806060", 6),
    ]
    for fclasses, fill, sz in items:
        r += rule(f"transport_{fclasses[0]}",
                  ogc_or("fclass", fclasses),
                  scale(Z17_MIN_SCALE_DENOM, 3500),
                  [point_sym(fill, sz),
                   text_sym("name", "Noto Sans, Arial, sans-serif", 9, fill,
                            "rgba(255,255,255,0.6)", 1)])
    return named_layer("gis_osm_transport_free_1", "Transport (Point) - OSM Carto z17", r)


def gen_transport_a():
    """gis_osm_transport_a_free_1.sld — Polygon (transport areas like airport apron)"""
    r = ""
    r += rule("transport_area_station",
              ogc_or("fclass", ["railway_station", "bus_station"]),
              scale(),
              polygon_sym("#d9d0c9", "#b0a7a0", 0.75))
    r += rule("transport_area_airport",
              ogc_or("fclass", ["airport", "airfield", "apron"]),
              scale(),
              polygon_sym("#dadae0", "#c0c0c8", 0.5))
    r += rule("transport_area_ferry",
              ogc_or("fclass", ["ferry_terminal"]),
              scale(),
              polygon_sym("#e9e7e2", "#c0c0c0", 0.5))
    return named_layer("gis_osm_transport_a_free_1", "Transport (Area) - OSM Carto z17", r)


def gen_traffic():
    """gis_osm_traffic_free_1.sld — Point"""
    r = ""
    items = [
        (["traffic_signals"], "#545454", 6, "square"),
        (["mini_roundabout"], "#ffffff", 8, "circle"),
        (["crossing"], "#0092da", 6, "square"),
        (["fuel"], "#0092da", 6, "square"),
        (["service"], "#0092da", 6, "square"),
        (["parking", "parking_surface", "parking_multistorey",
          "parking_underground", "parking_street"], "#0092da", 6, "square"),
        (["parking_bicycle", "bicycle_repair_station"], "#0092da", 6, "square"),
        (["slipway"], "#0092da", 6, "circle"),
        (["marina"], "#0092da", 8, "circle"),
        (["pier"], "#666666", 6, "square"),
        (["dam"], "#adadad", 8, "square"),
        (["waterfall"], "#0092da", 6, "triangle"),
        (["lock_gate", "weir"], "#aaa", 8, "square"),
        (["stop"], "#cc0000", 8, "hexagon"),
        (["turning_circle"], "#ffffff", 6, "circle"),
        (["speed_camera"], "#ffff00", 6, "square"),
        (["street_lamp"], "#ffff00", 4, "circle"),
        (["ford"], "#0092da", 6, "triangle"),
    ]
    for fclasses, fill, sz, shape in items:
        r += rule(f"traffic_{fclasses[0]}",
                  ogc_or("fclass", fclasses),
                  scale(),
                  point_sym(fill, sz, shape=shape))
    # Motorway junction with label
    r += rule("traffic_motorway_junction",
              ogc_or("fclass", ["motorway_junction"]),
              scale(),
              [point_sym("#cc0000", 6, shape="circle"),
               text_sym("name", "Noto Sans, Arial, sans-serif", 9, "#960000",
                        "rgba(255,255,255,0.6)", 1)])
    return named_layer("gis_osm_traffic_free_1", "Traffic (Point) - OSM Carto z17", r)


def gen_traffic_a():
    """gis_osm_traffic_a_free_1.sld — Polygon (parking areas, marinas, piers, dams)"""
    r = ""
    r += rule("traffic_area_parking",
              ogc_or("fclass", ["parking", "parking_surface", "parking_multistorey",
                                 "parking_underground", "parking_street"]),
              scale(),
              polygon_sym("#eeeeee", "#c0c0c0", 0.5))
    r += rule("traffic_area_marina",
              ogc_or("fclass", ["marina"]),
              scale(),
              polygon_sym("#aad3df", "#8080ff", 0.5))
    r += rule("traffic_area_pier",
              ogc_or("fclass", ["pier"]),
              scale(),
              polygon_sym("#f2efe9", "#c0c0c0", 0.5))
    r += rule("traffic_area_dam",
              ogc_or("fclass", ["dam"]),
              scale(),
              polygon_sym("#adadad", "#444444", 1))
    return named_layer("gis_osm_traffic_a_free_1", "Traffic (Area) - OSM Carto z17", r)


def gen_roads():
    """gis_osm_roads_free_1.sld — Line (casing+fill pattern)"""
    r = ""

    # Road definitions: (fclass, casing_color, casing_w, fill_color, fill_w, fill_dash)
    roads = [
        ("motorway",      "#dc2a67", 18, "#e892a2", 12, None),
        ("trunk",         "#c84e2f", 18, "#f9b29c", 12, None),
        ("primary",       "#a06b00", 18, "#fcd6a4", 12, None),
        ("secondary",     "#707d05", 18, "#f7fabf", 12, None),
        ("tertiary",      "#8f8f8f", 18, "#ffffff", 12, None),
        ("unclassified",  "#bbbbbb", 12, "#ffffff", 7,  None),
        ("residential",   "#bbbbbb", 12, "#ffffff", 7,  None),
        ("living_street", "#bbbbbb", 12, "#ededed", 7,  None),
        ("pedestrian",    "#999999", 12, "#dddde8", 7,  None),
        ("busway",        "#bbbbbb", 12, "#6699ff", 7,  None),
        ("service",       "#bbbbbb", 7,  "#ffffff", 5,  None),
        ("track",         "#ffffff", 1.5, "#996600", 1.2, None),
        ("bridleway",     "#ffffff", 1.2, "#008000", 0.8, "4,4"),
        ("cycleway",      "#ffffff", 0.9, "#0000ff", 0.6, "4,4"),
        ("footway",       "#ffffff", 1.3, "#fa8072", 0.9, "2,4"),
        ("path",          "#ffffff", 1.3, "#fa8072", 0.9, "2,4"),
        ("steps",         "#ffffff", 3,   "#fa8072", 2,   "2,3"),
        ("motorway_link", "#dc2a67", 12, "#e892a2", 10, None),
        ("trunk_link",    "#c84e2f", 12, "#f9b29c", 10, None),
        ("primary_link",  "#a06b00", 12, "#fcd6a4", 10, None),
        ("secondary_link","#707d05", 12, "#f7fabf", 10, None),
        ("tertiary_link", "#8f8f8f", 12, "#ffffff", 9,  None),
        ("unknown",       "#bbbbbb", 5,  "#dddddd", 3,  None),
    ]

    for fclass, c_color, c_w, f_color, f_w, f_dash in roads:
        # CASING FIRST (renders underneath)
        r += rule(f"road_{fclass}_casing",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  line_sym(c_color, c_w, cap="round"))
        # FILL SECOND (renders on top)
        r += rule(f"road_{fclass}_fill",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  line_sym(f_color, f_w, f_dash, cap="round"))

    # Track grade variants
    track_grades = [
        ("track_grade1", "#ffffff", 0.75, "#996600", 0.75, None),
        ("track_grade2", "#ffffff", 0.75, "#996600", 0.75, "6,3"),
        ("track_grade3", "#ffffff", 1.5,  "#996600", 1.2,  "4,3"),
        ("track_grade4", "#ffffff", 1.5,  "#996600", 1.2,  "4,3,2,3"),
        ("track_grade5", "#ffffff", 1.5,  "#996600", 1.2,  "1,3"),
    ]
    for fclass, c_color, c_w, f_color, f_w, f_dash in track_grades:
        r += rule(f"road_{fclass}_casing",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  line_sym(c_color, c_w, cap="round"))
        r += rule(f"road_{fclass}_fill",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  line_sym(f_color, f_w, f_dash, cap="round"))

    return named_layer("gis_osm_roads_free_1", "Roads (Line) - OSM Carto z17", r)


def gen_railways():
    """gis_osm_railways_free_1.sld — Line"""
    r = ""
    items = [
        ("rail",         "#666666", 2.5, None),
        ("light_rail",   "#666666", 2.5, None),
        ("subway",       "#666666", 2.5, "8,6"),
        ("tram",         "#666666", 1.5, None),
        ("monorail",     "#666666", 2.5, None),
        ("narrow_gauge", "#666666", 1.5, "6,6"),
        ("miniature",    "#666666", 1.0, "4,4"),
        ("funicular",    "#666666", 1.5, None),
        ("rack",         "#666666", 1.5, "4,2"),
        ("drag_lift",    "#806060", 0.8, None),
        ("chair_lift",   "#806060", 1.0, None),
        ("cable_car",    "#806060", 1.5, None),
        ("gondola",      "#806060", 1.5, None),
        ("goods",        "#806060", 1.0, None),
        ("other_lift",   "#806060", 0.8, None),
    ]
    for fclass, color, width, dash in items:
        r += rule(f"railway_{fclass}",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  line_sym(color, width, dash, join="round"))
    return named_layer("gis_osm_railways_free_1", "Railways (Line) - OSM Carto z17", r)


def gen_places():
    """gis_osm_places_free_1.sld — Point"""
    r = ""
    items = [
        ("city",      15, "#222222"),
        ("town",      13, "#222222"),
        ("suburb",    12, "#222222"),
        ("village",   12, "#222222"),
        ("hamlet",    10, "#222222"),
        ("island",    11, "#222222"),
        ("locality",  10, "#777777"),
        ("farm",      10, "#777777"),
        ("dwelling",  10, "#777777"),
        ("region",    13, "#777777"),
        ("county",    11, "#777777"),
        ("national_capital", 16, "#222222"),
    ]
    for fclass, sz, color in items:
        r += rule(f"place_{fclass}",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  text_sym("name", "Noto Sans, Arial, sans-serif", sz, color,
                           "rgba(255,255,255,0.6)", 1.5))
    return named_layer("gis_osm_places_free_1", "Places (Point) - OSM Carto z17", r)


def gen_places_a():
    """gis_osm_places_a_free_1.sld — Polygon (place boundaries)"""
    r = ""
    # Place boundaries are administrative-ish
    r += rule("place_area",
              ogc_or("fclass", ["city", "town", "suburb", "village"]),
              scale(),
              [polygon_sym("none", "#a37da1", 1.5, "4,4"),
               text_sym("name", "Noto Sans, Arial, sans-serif", 12, "#222222",
                        "rgba(255,255,255,0.6)", 1.5)])
    return named_layer("gis_osm_places_a_free_1", "Places (Area) - OSM Carto z17", r)


def gen_pois():
    """gis_osm_pois_free_1.sld — Point"""
    r = ""
    groups = [
        (["restaurant", "fast_food", "cafe", "pub", "bar", "food_court", "biergarten",
          "ice_rink"],
         "#C77400", 6, "gastronomy"),
        (["bank", "atm"], "#734a08", 6, "money"),
        (["hotel", "motel", "guesthouse", "hostel", "chalet", "bed_and_breakfast",
          "camp_site", "caravan_site", "alpine_hut", "shelter"],
         "#0092da", 6, "accommodation"),
        (["museum", "attraction", "monument", "memorial", "art", "castle", "ruins",
          "archaeological", "wayside_cross", "wayside_shrine", "battlefield", "fort",
          "picnic_site", "viewpoint", "zoo", "theme_park", "tourist_info", "tourist_map",
          "tourist_board", "tourist_guidepost"],
         "#734a08", 6, "tourism"),
        (["hospital", "pharmacy", "clinic", "doctors", "dentist", "veterinary"],
         "#BF0000", 6, "health"),
        (["university", "school", "kindergarten", "college", "library", "public_building"],
         "#734a08", 6, "education"),
        (["supermarket", "bakery", "mall", "convenience", "clothes", "bookshop",
          "butcher", "florist", "gift_shop", "department_store", "kiosk", "general",
          "chemist", "optician", "jeweller", "sports_shop", "stationery", "shoe_shop",
          "beverages", "greengrocer", "newsagent", "outdoor_shop", "mobile_phone_shop",
          "toy_shop", "video_shop", "beauty_shop", "car_dealership", "bicycle_shop",
          "doityourself", "furniture_shop", "computer_shop", "garden_centre"],
         "#ac39ac", 5, "shopping"),
        (["police", "fire_station", "post_office", "post_box", "town_hall",
          "courthouse", "prison", "embassy", "consulate", "community_centre",
          "nursing_home", "arts_centre", "market_place"],
         "#734a08", 6, "public"),
        (["theatre", "nightclub", "cinema"], "#734a08", 6, "culture"),
        (["sports_centre", "pitch", "stadium", "tennis_court", "swimming_pool",
          "golf_course"],
         "#0092da", 6, "sports"),
        (["park", "playground", "dog_park"], "#008000", 6, "leisure"),
        (["toilet", "bench", "drinking_water", "fountain", "waste_basket",
          "telephone",
          "recycling", "recycling_glass", "recycling_paper", "recycling_clothes",
          "recycling_metal", "graveyard", "hunting_stand", "fire_hydrant",
          "emergency_phone", "emergency_access", "camera_surveillance"],
         "#734a08", 5, "misc"),
        (["tower", "tower_comms", "water_tower", "tower_observation",
          "windmill", "lighthouse", "wastewater_plant", "water_well",
          "water_mill", "water_works"],
         "#666666", 6, "man_made"),
        (["vending_machine", "vending_cigarette", "vending_parking",
          "vending_drinks", "vending_tickets"],
         "#734a08", 5, "vending"),
        (["hairdresser", "car_repair", "car_rental", "car_wash", "car_sharing",
          "bicycle_rental", "travel_agent", "laundry"],
         "#ac39ac", 5, "services"),
    ]
    for fclasses, fill, sz, gname in groups:
        r += rule(f"poi_{gname}",
                  ogc_or("fclass", fclasses),
                  scale(Z17_MIN_SCALE_DENOM, 3500),
                  [point_sym(fill, sz),
                   text_sym("name", "Noto Sans, Arial, sans-serif", 9, fill,
                            "rgba(255,255,255,0.6)", 1)])
    return named_layer("gis_osm_pois_free_1", "POIs (Point) - OSM Carto z17", r)


def gen_pois_a():
    """gis_osm_pois_a_free_1.sld — Polygon (POI areas)"""
    r = ""
    # POI areas get building-style rendering + label
    area_pois = [
        (["university", "school", "kindergarten", "college"], "#ffffe5", "#d0d0a0"),
        (["hospital", "clinic"], "#ffffe5", "#d0d0a0"),
        (["place_of_worship", "christian", "jewish", "muslim", "buddhist", "hindu"],
         "#d0d0d0", "#9a9a9a"),
        (["supermarket", "mall", "department_store"], "#ffd6d1", "#d99c95"),
        (["police", "fire_station", "town_hall"], "#ffffe5", "#d0d0a0"),
        (["sports_centre", "stadium"], "#c8facc", "#a0d0a0"),
        (["swimming_pool"], "#aad3df", "#8080c0"),
        (["golf_course"], "#def6c0", "#a0c080"),
        (["restaurant", "fast_food", "cafe", "pub", "bar"], "#ffffe5", "#d0d0a0"),
        (["hotel", "motel", "guesthouse", "hostel"], "#ffffe5", "#d0d0a0"),
        (["museum", "library", "theatre", "cinema", "arts_centre"], "#ffffe5", "#d0d0a0"),
        (["grave_yard"], "#aacbaf", "#80a080"),
        (["market_place"], "#ffffe5", "#d0d0a0"),
        (["camp_site", "caravan_site"], "#def6c0", "#a0c080"),
    ]
    for fclasses, fill, stroke in area_pois:
        r += rule(f"pois_area_{fclasses[0]}",
                  ogc_or("fclass", fclasses),
                  scale(),
                  [polygon_sym(fill, stroke, 0.5),
                   text_sym("name", "Noto Sans, Arial, sans-serif", 10, "#555555",
                            "rgba(255,255,255,0.6)", 1)])
    return named_layer("gis_osm_pois_a_free_1", "POIs (Area) - OSM Carto z17", r)


def gen_pofw():
    """gis_osm_pofw_free_1.sld — Point"""
    r = ""
    all_pofw = [
        "place_of_worship", "christian", "christian_anglican", "christian_catholic",
        "christian_evangelical", "christian_lutheran", "christian_methodist",
        "christian_orthodox", "christian_protestant", "christian_baptist",
        "christian_mormon", "jewish", "muslim", "muslim_sunni", "muslim_shia",
        "buddhist", "hindu", "taoist", "shintoist", "sikh"
    ]
    r += rule("pofw_point",
              ogc_or("fclass", all_pofw),
              scale(Z17_MIN_SCALE_DENOM, 3500),
              [point_sym("#000000", 6),
               text_sym("name", "Noto Sans, Arial, sans-serif", 9, "#000000",
                        "rgba(255,255,255,0.6)", 1)])
    return named_layer("gis_osm_pofw_free_1", "Places of Worship (Point) - OSM Carto z17", r)


def gen_pofw_a():
    """gis_osm_pofw_a_free_1.sld — Polygon (religious building areas)"""
    r = ""
    all_pofw = [
        "place_of_worship", "christian", "christian_anglican", "christian_catholic",
        "christian_evangelical", "christian_lutheran", "christian_methodist",
        "christian_orthodox", "christian_protestant", "christian_baptist",
        "christian_mormon", "jewish", "muslim", "muslim_sunni", "muslim_shia",
        "buddhist", "hindu", "taoist", "shintoist", "sikh"
    ]
    r += rule("pofw_area",
              ogc_or("fclass", all_pofw),
              scale(),
              [polygon_sym("#d0d0d0", "#9a9a9a", 0.75),
               text_sym("name", "Noto Sans, Arial, sans-serif", 11, "#000000",
                        "rgba(255,255,255,0.6)", 1)])
    return named_layer("gis_osm_pofw_a_free_1", "Places of Worship (Area) - OSM Carto z17", r)


def gen_natural():
    """gis_osm_natural_free_1.sld — Point"""
    r = ""
    items = [
        ("peak", "#d08f55", 8, "triangle", True),
        ("volcano", "#d08f55", 10, "triangle", True),
        ("spring", "#aad3df", 6, "circle", False),
        ("cave_entrance", "#666666", 6, "circle", False),
        ("tree", "#add19e", 5, "circle", False),
        ("beach", "#fff1ba", 6, "circle", False),
        ("mine", "#666666", 6, "square", False),
        ("cliff", "#666666", 6, "square", False),
        ("glacier", "#ddecec", 6, "circle", False),
    ]
    for fclass, fill, sz, shape, has_label in items:
        syms = [point_sym(fill, sz, shape=shape)]
        if has_label:
            syms.append(text_sym("name", "Noto Sans, Arial, sans-serif", 10, "#222222",
                                 "rgba(255,255,255,0.6)", 1))
        r += rule(f"natural_{fclass}",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  syms)
    return named_layer("gis_osm_natural_free_1", "Natural Features (Point) - OSM Carto z17", r)


def gen_natural_a():
    """gis_osm_natural_a_free_1.sld — Polygon (beach, glacier, cliff areas)"""
    r = ""
    r += rule("natural_area_beach",
              ogc_or("fclass", ["beach"]),
              scale(),
              polygon_sym("#fff1ba", None))
    r += rule("natural_area_glacier",
              ogc_or("fclass", ["glacier"]),
              scale(),
              polygon_sym("#ddecec", "#9cf", 1.5, "4,2"))
    r += rule("natural_area_cliff",
              ogc_or("fclass", ["cliff"]),
              scale(),
              line_sym("#666666", 1.5))
    return named_layer("gis_osm_natural_a_free_1", "Natural Features (Area) - OSM Carto z17", r)


def gen_adminareas_a():
    """gis_osm_adminareas_a_free_1.sld — Polygon"""
    r = ""
    items = [
        ("admin_area",   "#a37da1", 1, 9),
        ("national",     "#8d618b", 7, 12),
        ("admin_level1", "#8d618b", 5, 11),
        ("admin_level3", "#a37da1", 3, 10),
        ("admin_level4", "#a37da1", 3, 10),
        ("admin_level5", "#a37da1", 2, 9),
        ("admin_level6", "#a37da1", 2, 9),
        ("admin_level7", "#a37da1", 1.5, 9),
        ("admin_level8", "#a37da1", 1.5, 9),
        ("admin_level9", "#a37da1", 1, 8),
        ("admin_level10","#a37da1", 0.5, 8),
        ("admin_level11","#a37da1", 0.5, 8),
    ]
    for fclass, color, width, font_sz in items:
        r += rule(f"admin_{fclass}",
                  ogc_or("fclass", [fclass]),
                  scale(),
                  [polygon_sym("none", color, width),
                   text_sym("name", "Noto Sans, Arial, sans-serif", font_sz, color,
                            "rgba(255,255,255,0.6)", 1.5)])
    return named_layer("gis_osm_adminareas_a_free_1", "Administrative Areas (Area) - OSM Carto z17", r)


def gen_protected_areas_a():
    """gis_osm_protected_areas_a_free_1.sld — Polygon"""
    r = ""
    all_protected = [
        "national_park", "other_nature_reserve",
        "icun_1", "icun_3", "icun_4", "icun_5", "icun_6", "icun_7", "icun_8"
    ]
    r += rule("protected_area",
              ogc_or("fclass", all_protected),
              scale(),
              [polygon_sym("none", "#a0d0a0", 1.5, "6,6"),
               text_sym("name", "Noto Sans, Arial, sans-serif", 10, "#008000",
                        "rgba(255,255,255,0.6)", 1)])
    return named_layer("gis_osm_protected_areas_a_free_1", "Protected Areas (Area) - OSM Carto z17", r)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

# Mapping: Geofabrik filename → generator function
ALL_LAYERS = {
    "gis_osm_water_a_free_1.sld":           gen_water_a,
    "gis_osm_waterways_free_1.sld":         gen_waterways,
    "gis_osm_transport_free_1.sld":         gen_transport,
    "gis_osm_transport_a_free_1.sld":       gen_transport_a,
    "gis_osm_traffic_free_1.sld":           gen_traffic,
    "gis_osm_traffic_a_free_1.sld":         gen_traffic_a,
    "gis_osm_roads_free_1.sld":             gen_roads,
    "gis_osm_railways_free_1.sld":          gen_railways,
    "gis_osm_protected_areas_a_free_1.sld": gen_protected_areas_a,
    "gis_osm_pois_free_1.sld":              gen_pois,
    "gis_osm_pois_a_free_1.sld":            gen_pois_a,
    "gis_osm_pofw_free_1.sld":              gen_pofw,
    "gis_osm_pofw_a_free_1.sld":            gen_pofw_a,
    "gis_osm_places_free_1.sld":            gen_places,
    "gis_osm_places_a_free_1.sld":          gen_places_a,
    "gis_osm_natural_free_1.sld":           gen_natural,
    "gis_osm_natural_a_free_1.sld":         gen_natural_a,
    "gis_osm_landuse_a_free_1.sld":         gen_landuse_a,
    "gis_osm_buildings_a_free_1.sld":       gen_buildings_a,
    "gis_osm_adminareas_a_free_1.sld":      gen_adminareas_a,
}


def main():
    parser = argparse.ArgumentParser(description="Generate SLD 1.0 files for Geofabrik OSM layers at z17")
    parser.add_argument("--layer", help="Generate only a specific layer (base name, e.g. 'roads')")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.layer:
        # Find matching filename(s)
        matched = [fn for fn in ALL_LAYERS if args.layer in fn]
        if not matched:
            print(f"No layer matching '{args.layer}' found.")
            print(f"Available: {', '.join(ALL_LAYERS.keys())}")
            return
        for fn in matched:
            filepath = os.path.join(OUTPUT_DIR, fn)
            content = SLD_HEADER + ALL_LAYERS[fn]() + SLD_FOOTER
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  OK {filepath}")
    else:
        for fn, gen_func in ALL_LAYERS.items():
            filepath = os.path.join(OUTPUT_DIR, fn)
            content = SLD_HEADER + gen_func() + SLD_FOOTER
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  OK {filepath}")

    print(f"\nDone. {len(ALL_LAYERS) if not args.layer else len(matched)} SLD files in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
