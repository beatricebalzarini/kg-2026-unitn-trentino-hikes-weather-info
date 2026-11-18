"""Generate data/entities/SCHEMA.md from the entity files: for every entity type, every field with its type,
how often it is filled, its values (or an example) and its meaning. Run by run_all.py after build_entities.py,
so the document always matches the data. Descriptions are written by hand in DOCS below.
"""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENT = HERE.parent / "data" / "entities"

ENTITIES = {  # file -> (EType, description, sources in data/clean)
    "routes": ("Route", "a path that can be followed from start to end",
               "trails, mtb, foot_routes, via_ferrata"),
    "segments": ("Segment", "one stretch of a route (an OSM way), shared by the routes it belongs to", "ways"),
    "landmarks": ("Landmark", "a natural or cultural point of interest that a route reaches or passes by",
                  "landmarks, lakes, glaciers, cultural_landmarks"),
    "hospitality": ("Hospitality", "a place where one can eat and/or sleep",
                    "huts (alpine and wilderness huts), accommodations, food_drink"),
    "facilities": ("Facility", "a service along the way",
                   "water_points, rest_areas, guideposts, tourist_info, huts (emergency shelters)"),
    "transport": ("Transport", "where one boards a means of transport, or a lift line",
                  "transport_stops, aerialways"),
    "municipalities": ("Municipality", "a municipality (comune) of the province", "municipalities"),
    "province": ("Province", "the Autonomous Province of Trento", "province"),
}

COMMON = {
    "id": "identifying attribute: `{osm type}/{osm id}` (e.g. `way/123`); ISTAT code for municipalities and the province; `via_ferrata/<slug>` for via ferrata rebuilt from several ways. It becomes the entity URI",
    "name": "label; unnamed objects get a generated label `{type} – {municipality}`",
    "name_source": "where `name` comes from: `name` (OSM name), `name_stage` (OSM name + stage), `name_disambiguated` (OSM name + basin/part/municipality to make it unique), `ref_from_to` / `ref` / `from_to` (built from the trail number and places), `generated`",
    "name_osm": "the OSM `name` tag, when there is one",
    "category": "the subtype of the entity (see the values)",
    "ele_m": "elevation in metres",
    "ele_source": "`tag` (from OSM); `dem` will be used by the planned DEM enrichment",
    "lat": "latitude (WGS84) of the representative point",
    "lon": "longitude (WGS84) of the representative point",
    "municipality_istat": "ISTAT code of the municipality containing the point (→ municipalities.id)",
    "wikidata": "Wikidata QID, for external linking",
    "source_dataset": "the raw OSM export the entity comes from (in `data/`)",
    "merged_osm_ids": "other OSM objects merged into this entity (the same real object mapped more than once): list of `{osm_id, file}`, `file` = cleaned file in `data/clean/` where it was",
    "operator": "list of operators, normalized (SAT, CAI, AVS, Trentino Trasporti, ...)",
    "wheelchair": "`yes` / `limited` / `no` (OSM tag)",
    "opening_hours": "OSM opening hours (free syntax)",
    "subtype": "finer type inside the category",
    "capacity": "number of places/beds",
}
DOCS = {
    "routes": {
        "ref": "trail number (e.g. SAT number)", "reg_ref": "SAT cadastre code (E/O + number)",
        "from": "start place (text)", "to": "end place (text)", "description": "OSM description",
        "cai_scale": "CAI hiking difficulty: T, E, EE, EEA", "ferrata_grade": "grade of an EEA trail: F, PD, MD, D",
        "via_ferrata_scale": "via ferrata difficulty (0–6, with +/-)", "via_ferrata_scale_source": "`relation` or `ways_max`",
        "mtb_scale": "MTB difficulty 0–6", "cai_scale_mtb": "CAI MTB difficulty (MC, OC, ...)",
        "sac_scale_max": "highest SAC difficulty of the segments (via ferrata, 0–6)",
        "distance_km": "declared length (OSM tag)", "distance_source": "`distance` or `length` tag",
        "length_km": "length computed from the geometry", "duration_forward_min": "declared walking time, forward",
        "duration_backward_min": "declared walking time, backward", "ascent_m": "declared ascent",
        "descent_m": "declared descent", "ele_from_m": "elevation of the start", "ele_to_m": "elevation of the end",
        "ele_max_m": "highest elevation", "ele_min_m": "lowest elevation", "roundtrip": "loop route",
        "roundtrip_source": "`tag`, or `geometry` (start and end within 50 m)", "start": "start point {lat, lon}",
        "end": "end point {lat, lon}", "segment_ids": "ids of the segments, in order (→ segments.id): relation hasSegment",
        "guidepost_ids": "ids of the guideposts of the route (→ facilities.id, when present)",
        "province_rule": "why it is in Trentino: `endpoint` (starts/ends inside) or `length_50` (≥ 50% inside)",
        "osm_relation_id": "OSM relation of a rebuilt via ferrata", "name_variants": "spellings merged into one via ferrata",
    },
    "segments": {
        "highway": "OSM way type (path, track, residential, steps, via_ferrata, ...)",
        "aerialway": "lift type, when the segment is a lift", "length_m": "length computed from the geometry",
        "surface": "OSM surface (only from the tag)", "surface_class": "`paved` / `unpaved`",
        "surface_source": "`tag`, `inferred_highway`, `inferred_tracktype`", "smoothness": "1 (excellent) – 8 (impassable)",
        "incline_pct": "absolute slope in % (numeric tags only)", "width_m": "width in metres",
        "sac_scale": "SAC hiking difficulty 0–6", "mtb_scale": "MTB difficulty 0–6",
        "bicycle_allowed": "bicycles allowed", "stroller": "stroller tag (rare)",
        "via_ferrata_scale": "via ferrata difficulty",
    },
    "landmarks": {
        "landmark_type": "`natural` or `cultural`", "mountain_pass": "the saddle is a mountain pass",
        "area_km2": "area (lakes, glaciers)", "area_inside_pct": "% of the area inside Trentino (lakes, glaciers)",
        "swimming": "swimming allowed (lakes)", "fishing": "`yes` / `no` / `license` (lakes)", "boat": "boats allowed (lakes)",
        "municipalities_istat": "ISTAT codes of the Trentino municipalities touched (→ municipalities.id); a lake can touch several",
    },
    "hospitality": {
        "overnight": "one can sleep there (huts, bivouacs, accommodations)",
        "food_service": "one can eat there: true only if stated (restaurant category or a tag), else null = not verified",
        "food_service_source": "`category`, `tag`, `duplicate_food_drink`", "cuisine": "list of cuisines",
        "capacity_source": "`capacity` or `beds` tag", "stars": "hotel stars (integer)", "rooms": "number of rooms",
        "winter_room": "hut with a winter room", "capacity_pitches": "camp site pitches", "tents": "camp site: tents",
        "caravans": "camp site: caravans", "motorhome": "camp site: motorhomes", "fee": "fee required (huts)",
        "dog": "dogs allowed", "internet_access": "internet available", "outdoor_seating": "outdoor seating",
        "takeaway": "`yes` / `no` / `only`", "diet_vegetarian": "`yes` / `no` / `limited` / `only`",
        "diet_vegan": "`yes` / `no` / `limited` / `only`", "diet_gluten_free": "`yes` / `no` / `limited` / `only`",
        "phone": "list of phone numbers (+39...)", "email": "e-mail", "website": "website",
    },
    "facilities": {
        "drinking": "drinkable water (water points)", "on_kept_route": "the guidepost belongs to a route of routes.json",
    },
    "transport": {
        "mode": "`bus`, `train`, `funicular`, `aerialway`", "has_shelter": "the stop has a shelter",
        "has_shelter_source": "`tag` or `pending_bus_shelter` (matched shelter within 30 m)",
        "summer_access": "lifts: usable in summer (`no`, `both`, `entry`, `exit`)", "duration_min": "lift ride time (lift lines)",
    },
    "municipalities": {
        "osm_id": "OSM relation", "province_id": "→ province.id: relation partOf", "postal_code": "postal code (CAP)",
        "centre_source": "`admin_centre` or `polygon_centroid`", "bounds": "bounding box",
    },
    "province": {
        "osm_id": "OSM relation", "iso3166_2": "ISO code", "admin_centre_osm_id": "OSM node of Trento",
        "municipality_ids": "ISTAT codes of its municipalities (→ municipalities.id)", "bounds": "bounding box",
    },
}
REFERENCES = [
    ("routes.segment_ids", "segments.id", "hasSegment (in the data)"),
    ("routes.guidepost_ids", "facilities.id", "passesBy, guideposts (in the data; 417 of 506 references are in facilities)"),
    ("landmarks.municipalities_istat", "municipalities.id", "locatedIn"),
    ("hospitality / facilities / transport.municipality_istat", "municipalities.id", "locatedIn"),
    ("municipalities.province_id", "province.id", "partOf"),
    ("routes ↔ landmarks / facilities / hospitality / transport / municipalities", "–",
     "passesBy, nearTo, startsNear, crosses: spatial joins, to be computed (Phase 4)"),
    ("transport (lift line) ↔ transport (lift station)", "–", "hasStation: spatial join, to be computed"),
]
GEOMETRY = {
    "routes_geometry.geojson": "line of every route (property `id` → routes.id)",
    "landmarks_geometry.geojson": "polygon of every lake and glacier (property `id` → landmarks.id)",
    "municipalities_boundaries.geojson": "polygon of every municipality (property `id` → municipalities.id)",
    "province_boundary.geojson": "polygon of the province (property `id` → province.id)",
}


def type_of(values):
    t = Counter("null" if v is None else type(v).__name__.replace("str", "string").replace("bool", "boolean")
                .replace("dict", "object").replace("list", "list") for v in values)
    return " / ".join(k for k in t if k != "null") or "null"


def values_of(vals):
    filled = [v for v in vals if v is not None]
    if not filled:
        return "–"
    if isinstance(filled[0], (dict, list)):
        ex = json.dumps(filled[0], ensure_ascii=False)
        return f"e.g. `{ex[:60]}{'…' if len(ex) > 60 else ''}`"
    c = Counter(filled)
    if len(c) <= 12 and not isinstance(filled[0], float):
        return ", ".join(f"`{k}` {n}" for k, n in c.most_common())
    if isinstance(filled[0], (int, float)) and not isinstance(filled[0], bool):
        return f"{min(filled)} – {max(filled)}"
    return f"e.g. `{str(filled[0])[:50]}`"


lines = ["# Entity files — schema", "",
         "Generated by `cleaning/schema_report.py` from the files in this folder (do not edit by hand: rerun "
         "`cleaning/run_all.py`). One file per entity type of `Phase 1 - Purpose Definition/ER-model.md`. "
         "OSM data © OpenStreetMap contributors, ODbL.", "",
         "Every row of a file has the same fields in the same order; `null` = not applicable or not known "
         "(a value not stated by a tag is never guessed). Derived Route attributes of the ER model "
         "(`paved_pct`, `max_incline_pct`, `stroller_suitable`, `wheelchair_suitable`) are not computed yet "
         "(integration step).", "", "## Overview", "",
         "| File | EType | Entities | Fields | Built from (`data/clean/`) |", "|---|---|---|---|---|"]
data = {f: json.load(open(ENT / f"{f}.json", encoding="utf-8")) for f in ENTITIES}
for f, (et, _, src) in ENTITIES.items():
    lines.append(f"| `{f}.json` | {et} | {len(data[f])} | {len(data[f][0])} | {src} |")
lines += [f"| **total** | | **{sum(len(v) for v in data.values())}** | | |", "",
          "## References between files", "", "| From | To | Relationship |", "|---|---|---|"]
lines += [f"| `{a}` | `{b}` | {c} |" for a, b, c in REFERENCES]
lines += ["", "Geometry files:", ""] + [f"- `{k}`: {v}" for k, v in GEOMETRY.items()]

for f, (et, desc, src) in ENTITIES.items():
    rows = data[f]
    lines += ["", f"## {et} — `{f}.json` ({len(rows)})", "", f"{desc[0].upper() + desc[1:]}. Built from: {src}.", "",
              "| Field | Type | Filled | Values | Meaning |", "|---|---|---|---|---|"]
    for k in rows[0]:
        vals = [r[k] for r in rows]
        filled = sum(v is not None for v in vals)
        meaning = DOCS[f].get(k) or COMMON.get(k, "")
        lines.append(f"| `{k}` | {type_of(vals)} | {100 * filled / len(rows):.0f}% | {values_of(vals)} | {meaning} |")

(ENT / "SCHEMA.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
missing = [(f, k) for f in ENTITIES for k in data[f][0] if not (DOCS[f].get(k) or COMMON.get(k))]
print("SCHEMA.md written;", "fields without a description:", missing or "none")
