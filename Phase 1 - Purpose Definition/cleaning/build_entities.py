"""Build one file per entity type of the ER model (ER-model.md) from the cleaned files in data/clean/.

Input:  data/clean/*.json, *_geometry.geojson (outputs of the clean_*.py scripts and dedup_cross_files.py)
Output: data/entities/{routes,segments,landmarks,hospitality,facilities,transport,municipalities,province}.json
        data/entities/{routes,landmarks}_geometry.geojson, municipalities_boundaries.geojson, province_boundary.geojson

Uniform schema (same in every file, see data/entities/SCHEMA.md):
  - `id` first; `name`, `name_source`, `name_osm`, `category` next; position, municipality, provenance last;
  - every row of a file has the same fields in the same order (null when not applicable);
  - `name_source` vocabulary: name, name_stage, name_disambiguated, ref_from_to, ref, from_to, generated;
  - `merged_osm_ids` = [{"osm_id", "file"}] of the other OSM objects merged into this entity (same structure
    mapped several times, in the same cleaned file or in another one); `ele_source` = "tag" when `ele_m` is set;
  - `source_dataset` = the raw OSM export the entity comes from.
"""
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLEAN = HERE.parent / "data" / "clean"
OUT = HERE.parent / "data" / "entities"
OUT.mkdir(parents=True, exist_ok=True)

NAME_SOURCE = {"name": "name", "osm": "name", "name_stage": "name_stage", "osm_basin": "name_disambiguated",
               "osm_part": "name_disambiguated", "osm_municipality": "name_disambiguated",
               "ref_from_to": "ref_from_to", "ref": "ref", "from_to": "from_to",
               "osm_id": "generated", "generated": "generated"}
RAW = {  # cleaned file -> raw OSM export
    "trails": "trails.json", "mtb": "mtb.json", "foot_routes": "stroller.json",
    "via_ferrata": "via_ferrata_routes.json", "huts": "huts_landmarks.json", "landmarks": "huts_landmarks.json",
    "food_drink": "amenities.json", "lakes": "lakes_geom.json", "glaciers": "lakes_geom.json",
    "water_points": "mixed_pois.json", "cultural_landmarks": "mixed_pois.json", "guideposts": "mixed_pois.json",
    "tourist_info": "mixed_pois.json", "rest_areas": "huts_landmarks.json",
    "transport_stops": "public_transportation.json", "aerialways": "public_transportation.json",
    "municipalities": "municipalities.json", "province": "province_boundaries.json",
}


def load(name):
    return json.load(open(CLEAN / f"{name}.json", encoding="utf-8"))


def name_fields(r):
    """-> name, name_source, name_osm (the OSM `name` tag when there is one)"""
    src = NAME_SOURCE[r.get("name_source") or "name"]
    if src == "name":
        osm = r["name"]
    elif src == "name_stage":
        osm = r["name"].split(" – Tappa ")[0]
    elif src == "name_disambiguated":
        osm = r.get("name_osm")
    else:
        osm = None
    return {"name": r["name"], "name_source": src, "name_osm": osm}


def merged(r, file):
    """merged_osm_ids (same file, ids only) + duplicates (other files) -> [{"osm_id", "file"}]"""
    own = r.get("osm_id") or r.get("id")
    items = [{"osm_id": i, "file": f"{file}.json"} for i in (r.get("merged_osm_ids") or []) if i != own]
    items += r.get("duplicates") or []
    return items or None


def ele(r, key="ele_m"):
    return {"ele_m": r.get(key), "ele_source": "tag" if r.get(key) is not None else None}


def point(r):
    return {"lat": float(r["lat"]), "lon": float(r["lon"])}


def common_tail(r, file):
    return {"wikidata": r.get("wikidata"), "source_dataset": r.get("source_dataset") or RAW[file],
            "merged_osm_ids": merged(r, file)}


def uniform(rows, order):
    """same keys, same order, in every row"""
    extra = [k for r in rows for k in r if k not in order]
    assert not extra, f"fields not in the schema: {sorted(set(extra))}"
    return [{k: r.get(k) for k in order} for r in rows]


# =============================== ROUTE ===============================
ROUTE_ORDER = ["id", "name", "name_source", "name_osm", "category", "ref", "reg_ref", "from", "to", "description",
               "operator", "cai_scale", "ferrata_grade", "via_ferrata_scale", "via_ferrata_scale_source",
               "mtb_scale", "cai_scale_mtb", "sac_scale_max", "distance_km", "distance_source", "length_km",
               "duration_forward_min", "duration_backward_min", "ascent_m", "descent_m", "ele_from_m", "ele_to_m",
               "ele_max_m", "ele_min_m", "ele_source", "roundtrip", "roundtrip_source", "start", "end",
               "segment_ids", "guidepost_ids", "province_rule", "osm_relation_id", "name_variants",
               "wikidata", "source_dataset", "merged_osm_ids"]
routes = []
for file, cat in [("trails", "trail"), ("mtb", None), ("foot_routes", "foot"), ("via_ferrata", "via_ferrata")]:
    for r in load(file):
        x = {k: v for k, v in r.items() if k in ROUTE_ORDER}
        has_ele = any(r.get(k) is not None for k in ("ele_from_m", "ele_to_m", "ele_max_m", "ele_min_m"))
        x.update({
            "id": r.get("osm_id") or r["id"], **name_fields(r), "category": cat or r["kind"],
            "distance_source": r.get("distance_source") or ("distance" if r.get("distance_km") is not None else None),
            "length_km": r["length_km_computed"], "ele_source": "tag" if has_ele else None,
            "segment_ids": r["main_way_ids"], "guidepost_ids": r.get("guidepost_node_ids") or None,
            **common_tail(r, file),
        })
        routes.append(x)
routes = uniform(routes, ROUTE_ORDER)

# =============================== SEGMENT ===============================
SEGMENT_ORDER = ["id", "highway", "aerialway", "length_m", "surface", "surface_class", "surface_source",
                 "smoothness", "incline_pct", "width_m", "sac_scale", "mtb_scale", "bicycle_allowed",
                 "wheelchair", "stroller", "via_ferrata_scale", "source_dataset"]
segments = []
for r in load("ways"):
    x = {k: v for k, v in r.items() if k in SEGMENT_ORDER}
    x.update({"id": r["osm_id"], "stroller": {"yes": True, "no": False}.get(r["stroller"])})
    segments.append(x)
segments = uniform(segments, SEGMENT_ORDER)

# =============================== LANDMARK ===============================
LANDMARK_ORDER = ["id", "name", "name_source", "name_osm", "category", "landmark_type", "subtype",
                  "mountain_pass", "area_km2", "area_inside_pct", "swimming", "fishing", "boat",
                  "ele_m", "ele_source", "lat", "lon", "municipalities_istat",
                  "wikidata", "source_dataset", "merged_osm_ids"]
landmarks = []
for file, ltype, cat in [("landmarks", "natural", None), ("lakes", "natural", "lake"),
                         ("glaciers", "natural", "glacier"), ("cultural_landmarks", "cultural", None)]:
    for r in load(file):
        x = {k: v for k, v in r.items() if k in LANDMARK_ORDER}
        x.update({"id": r["osm_id"], **name_fields(r), "category": cat or r["category"], "landmark_type": ltype,
                  **ele(r), **point(r),
                  "municipalities_istat": r.get("municipalities_istat") or [r["municipality_istat"]],
                  **common_tail(r, file)})
        landmarks.append(x)
landmarks = uniform(landmarks, LANDMARK_ORDER)

# =============================== HOSPITALITY ===============================
HOSP_ORDER = ["id", "name", "name_source", "name_osm", "category", "overnight", "food_service",
              "food_service_source", "cuisine", "capacity", "capacity_source", "stars", "rooms", "winter_room",
              "capacity_pitches", "tents", "caravans", "motorhome", "opening_hours", "fee", "wheelchair", "dog",
              "internet_access", "outdoor_seating", "takeaway", "diet_vegetarian", "diet_vegan",
              "diet_gluten_free", "operator", "phone", "email", "website",
              "ele_m", "ele_source", "lat", "lon", "municipality_istat",
              "wikidata", "source_dataset", "merged_osm_ids"]
hospitality, facilities = [], []
for r in load("huts"):
    if r["category"] == "emergency_shelter":
        facilities.append(("huts", r))            # emergency shelters are a Facility (ER-model.md)
        continue
    x = {k: v for k, v in r.items() if k in HOSP_ORDER}
    x.update({"id": r["osm_id"], **name_fields(r), "overnight": True, **ele(r), **point(r), **common_tail(r, "huts")})
    hospitality.append(x)
for r in load("accommodations"):
    x = {k: v for k, v in r.items() if k in HOSP_ORDER}
    x.update({"id": r["osm_id"], **name_fields(r), "overnight": True, **ele(r), **point(r),
              **common_tail(r, "accommodations")})
    hospitality.append(x)
for r in load("food_drink"):
    x = {k: v for k, v in r.items() if k in HOSP_ORDER}
    x.update({"id": r["osm_id"], **name_fields(r), "overnight": False,
              "food_service": True, "food_service_source": "category", **point(r), **common_tail(r, "food_drink")})
    hospitality.append(x)
hospitality = uniform(hospitality, HOSP_ORDER)

# =============================== FACILITY ===============================
FAC_ORDER = ["id", "name", "name_source", "name_osm", "category", "subtype", "drinking", "on_kept_route",
             "capacity", "operator", "ele_m", "ele_source", "lat", "lon", "municipality_istat",
             "wikidata", "source_dataset", "merged_osm_ids"]
fac_rows = []
for file, r in facilities:                                           # emergency shelters
    fac_rows.append({"id": r["osm_id"], **name_fields(r), "category": "emergency_shelter", "capacity": r["capacity"],
                     "operator": r["operator"], **ele(r), **point(r), "municipality_istat": r["municipality_istat"],
                     **common_tail(r, file)})
for file, cat in [("water_points", "water_point"), ("rest_areas", "rest_area"), ("guideposts", "guidepost"),
                  ("tourist_info", "tourist_info")]:
    for r in load(file):
        sub = r.get("type") if file == "rest_areas" else (r["category"] if file in ("water_points", "tourist_info") else None)
        fac_rows.append({"id": r["osm_id"], **name_fields(r), "category": cat, "subtype": sub,
                         "drinking": r.get("drinking"), "on_kept_route": r.get("on_kept_route"),
                         **ele(r), **point(r), "municipality_istat": r["municipality_istat"],
                         **common_tail(r, file)})
facilities = uniform(fac_rows, FAC_ORDER)

# =============================== TRANSPORT ===============================
TRANS_ORDER = ["id", "name", "name_source", "name_osm", "category", "mode", "operator", "has_shelter",
               "has_shelter_source", "wheelchair", "summer_access", "duration_min",
               "ele_m", "ele_source", "lat", "lon", "municipality_istat", "wikidata", "source_dataset", "merged_osm_ids"]
STOP_CAT = {("bus", "stop"): "bus_stop", ("bus", "station"): "bus_station", ("train", "station"): "train_station",
            ("funicular", "station"): "funicular_station", ("aerialway", "station"): "lift_station"}
transport = []
for r in load("transport_stops"):
    x = {k: v for k, v in r.items() if k in TRANS_ORDER}
    x.update({"id": r["osm_id"], **name_fields(r), "category": STOP_CAT[(r["mode"], r["kind"])], **ele(r),
              **point(r), **common_tail(r, "transport_stops")})
    transport.append(x)
for r in load("aerialways"):
    x = {k: v for k, v in r.items() if k in TRANS_ORDER}
    x.update({"id": r["osm_id"], **name_fields(r),
              "category": "lift_unknown" if r["type"] == "unknown" else r["type"], "mode": "aerialway",
              **point(r), **common_tail(r, "aerialways")})
    transport.append(x)
transport = uniform(transport, TRANS_ORDER)

# =============================== MUNICIPALITY / PROVINCE ===============================
MUNI_ORDER = ["id", "name", "name_source", "name_osm", "osm_id", "province_id", "postal_code",
              "lat", "lon", "centre_source", "bounds", "wikidata", "source_dataset"]
municipalities = uniform([{
    "id": r["istat"], **name_fields(r), "osm_id": r["osm_id"], "province_id": r["province_istat"],
    "postal_code": r["postal_code"], "lat": r["centre"]["lat"], "lon": r["centre"]["lon"],
    "centre_source": r["centre_source"], "bounds": r["bounds"], "wikidata": r["wikidata"],
    "source_dataset": RAW["municipalities"]} for r in load("municipalities")], MUNI_ORDER)
p = json.load(open(CLEAN / "province.json", encoding="utf-8"))
PROV_ORDER = ["id", "name", "name_source", "name_osm", "osm_id", "iso3166_2", "lat", "lon", "admin_centre_osm_id",
              "municipality_ids", "bounds", "wikidata", "source_dataset"]
province = uniform([{
    "id": p["istat"], "name": p["name"], "name_source": "name", "name_osm": p["name"], "osm_id": p["osm_id"],
    "iso3166_2": p["iso3166_2"], "lat": p["admin_centre"]["lat"], "lon": p["admin_centre"]["lon"],
    "admin_centre_osm_id": p["admin_centre"]["osm_id"],
    "municipality_ids": sorted(m["id"] for m in municipalities if m["province_id"] == p["istat"]),
    "bounds": p["bounds"], "wikidata": p["wikidata"], "source_dataset": RAW["province"]}], PROV_ORDER)

ENTITIES = {"routes": routes, "segments": segments, "landmarks": landmarks, "hospitality": hospitality,
            "facilities": facilities, "transport": transport, "municipalities": municipalities, "province": province}

# =============================== checks ===============================
for name, rows in ENTITIES.items():
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), f"{name}: duplicate ids"
    assert all(r["name_source"] in set(NAME_SOURCE.values()) for r in rows if "name_source" in r), name
seg_ids = {s["id"] for s in segments}
assert all(set(r["segment_ids"]) <= seg_ids for r in routes), "route segment not in segments"
istat = {m["id"] for m in municipalities}
for name in ("hospitality", "facilities", "transport"):
    assert all(r["municipality_istat"] in istat for r in ENTITIES[name]), name
assert all(set(r["municipalities_istat"]) <= istat for r in landmarks)
assert set(province[0]["municipality_ids"]) == istat
fac_ids = {f["id"] for f in facilities}
refs = {g for r in routes for g in (r["guidepost_ids"] or [])}

# =============================== write ===============================
for name, rows in ENTITIES.items():
    json.dump(rows, open(OUT / f"{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def regeo(files, key, extra=None):
    feats = []
    for f in files:
        for ft in json.load(open(CLEAN / f, encoding="utf-8"))["features"]:
            props = {"id": ft["properties"][key], **(extra(ft) if extra else {})}
            feats.append({"type": "Feature", "properties": props, "geometry": ft["geometry"]})
    return {"type": "FeatureCollection", "features": feats}


route_cat = {r["id"]: (r["category"], r["name"]) for r in routes}
land_name = {l["id"]: (l["category"], l["name"]) for l in landmarks}
outputs = {
    "routes_geometry.geojson": regeo(["trails_geometry.geojson", "mtb_geometry.geojson", "foot_routes_geometry.geojson"],
                                     "osm_id", lambda ft: dict(zip(("category", "name"), route_cat[ft["properties"]["osm_id"]]))),
    "landmarks_geometry.geojson": regeo(["lakes_geometry.geojson", "glaciers_geometry.geojson"], "osm_id",
                                        lambda ft: dict(zip(("category", "name"), land_name[ft["properties"]["osm_id"]]))),
    "municipalities_boundaries.geojson": regeo(["municipalities_boundaries.geojson"], "istat",
                                               lambda ft: {"name": ft["properties"]["name"]}),
    "province_boundary.geojson": regeo(["province_boundary.geojson"], "istat",
                                       lambda ft: {"name": ft["properties"]["name"]}),
}
vf = regeo(["via_ferrata_geometry.geojson"], "id", lambda ft: dict(zip(("category", "name"), route_cat[ft["properties"]["id"]])))
outputs["routes_geometry.geojson"]["features"] += vf["features"]
for f, fc in outputs.items():
    json.dump(fc, open(OUT / f, "w", encoding="utf-8"), ensure_ascii=False)
assert len(outputs["routes_geometry.geojson"]["features"]) == len(routes)

# =============================== report ===============================
total = 0
for name, rows in ENTITIES.items():
    total += len(rows)
    cats = Counter(r.get("category") for r in rows) if "category" in rows[0] else {}
    print(f"{name:15} {len(rows):6}  fields: {len(rows[0]):2}  {dict(cats) if len(cats) <= 16 else f'{len(cats)} categories'}")
print(f"{'TOTAL':15} {total:6}")
print(f"route guidepost references found in facilities: {len(refs & fac_ids)} of {len(refs)}")
print("written:", ", ".join(sorted(p.name for p in OUT.glob('*.json*'))))
