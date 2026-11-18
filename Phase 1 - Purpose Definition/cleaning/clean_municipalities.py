"""Clean municipalities.json.

Input:  data/municipalities.json (Overpass export, 166 relations, admin_level=8)
Output: data/clean/municipalities.json                -> municipality entities (flat attributes)
        data/clean/municipalities_boundaries.geojson  -> one (multi)polygon per municipality
"""
import json
from pathlib import Path

from shapely.geometry import LineString, Point, mapping
from shapely.ops import polygonize, unary_union

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "municipalities.json"
PROV = BASE / "data" / "clean" / "province_boundary.geojson"
OUT = BASE / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)

PROVINCE_ISTAT = "022"


def ring_polygons(members, role):
    lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
             for m in members
             if m["type"] == "way" and m["role"] == role and len(m.get("geometry", [])) >= 2]
    return list(polygonize(unary_union(lines))) if lines else []


def build_geometry(members):
    outer = unary_union(ring_polygons(members, "outer"))
    inner = ring_polygons(members, "inner")
    return outer.difference(unary_union(inner)) if inner else outer


elements = json.load(open(SRC, encoding="utf-8"))["elements"]
entities, features, problems = [], [], []

for el in elements:
    t = el["tags"]
    geom = build_geometry(el["members"])
    if geom.is_empty or not geom.is_valid:
        problems.append((t["name"], "invalid or empty geometry"))

    centre = next((m for m in el["members"] if m["role"] == "admin_centre"), None)
    if centre:
        lat, lon, src = centre["lat"], centre["lon"], "admin_centre"
    else:
        c = geom.centroid
        lat, lon, src = round(c.y, 7), round(c.x, 7), "polygon_centroid"
    if not geom.buffer(1e-4).contains(Point(lon, lat)):
        problems.append((t["name"], f"centre ({src}) outside its polygon"))

    entities.append({
        "istat": t["ref:ISTAT"],
        "osm_id": f"relation/{el['id']}",
        "name": t["name"],
        "province_istat": PROVINCE_ISTAT,
        "postal_code": t["admin_centre:postal_code"],
        "wikidata": t["wikidata"],
        "centre": {"lat": lat, "lon": lon},
        "centre_source": src,
        "bounds": el["bounds"],
    })
    features.append({
        "type": "Feature",
        "properties": {"istat": t["ref:ISTAT"], "osm_id": f"relation/{el['id']}", "name": t["name"]},
        "geometry": mapping(geom),
    })

# ---------- checks ----------
assert len({e["istat"] for e in entities}) == len(entities), "duplicate ISTAT codes"
assert all(e["istat"].startswith(PROVINCE_ISTAT) for e in entities)

from shapely.geometry import shape
province = shape(json.load(open(PROV, encoding="utf-8"))["features"][0]["geometry"])
union = unary_union([shape(f["geometry"]) for f in features])
diff = province.symmetric_difference(union).area
print(f"municipalities: {len(entities)} | centroid fallback: "
      f"{[e['name'] for e in entities if e['centre_source'] != 'admin_centre']}")
print(f"union vs province: symmetric difference = {diff / province.area:.6%} of province area")
print("problems:", problems or "none")

entities.sort(key=lambda e: e["istat"])
features.sort(key=lambda f: f["properties"]["istat"])
json.dump(entities, open(OUT / "municipalities.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump({"type": "FeatureCollection", "features": features},
          open(OUT / "municipalities_boundaries.geojson", "w", encoding="utf-8"), ensure_ascii=False)
print("written:", OUT / "municipalities.json", OUT / "municipalities_boundaries.geojson")
