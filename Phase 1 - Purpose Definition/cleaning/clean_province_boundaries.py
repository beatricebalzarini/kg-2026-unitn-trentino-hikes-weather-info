"""Clean province_boundaries.json.

Input:  data/province_boundaries.json (Overpass export, 1 relation)
Output: data/clean/province.json            -> province entity (flat attributes)
        data/clean/province_boundary.geojson -> province polygon (used as spatial filter)
"""
import json
from pathlib import Path

from shapely.geometry import LineString, Point, mapping
from shapely.ops import polygonize, unary_union

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "province_boundaries.json"
MUNI = BASE / "data" / "municipalities.json"
OUT = BASE / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)

raw = json.load(open(SRC, encoding="utf-8"))
rel = raw["elements"][0]
tags = rel["tags"]
members = rel["members"]

# ---------- polygon from the outer ways ----------
lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
         for m in members
         if m["type"] == "way" and m["role"] == "outer" and len(m.get("geometry", [])) >= 2]
polys = list(polygonize(unary_union(lines)))
polygon = unary_union(polys)
assert polygon.is_valid, "invalid province polygon"
print(f"outer ways: {len(lines)} | polygons: {len(polys)} | geometry: {polygon.geom_type}")

# ---------- entity ----------
centre = next(m for m in members if m["role"] == "admin_centre")
muni_ids = [f"relation/{m['ref']}" for m in members if m["type"] == "relation" and m["role"] == "subarea"]

province = {
    "osm_id": f"relation/{rel['id']}",
    "name": tags["official_name"],
    "istat": tags["ref:ISTAT"],
    "iso3166_2": tags["ISO3166-2"],
    "wikidata": tags["wikidata"],
    "admin_centre": {"osm_id": f"node/{centre['ref']}", "lat": centre["lat"], "lon": centre["lon"]},
    "bounds": rel["bounds"],
    "municipality_osm_ids": muni_ids,
}

# ---------- checks ----------
assert polygon.contains(Point(centre["lon"], centre["lat"])), "Trento not inside polygon"
muni = json.load(open(MUNI, encoding="utf-8"))["elements"]
muni_by_id = {m["id"]: m for m in muni}
missing = [i for i in muni_ids if int(i.split("/")[1]) not in muni_by_id]
centres = [(m["id"], mm) for m in muni for mm in m["members"] if mm.get("role") == "admin_centre"]
outside = [(i, c["lat"], c["lon"]) for i, c in centres
           if not polygon.buffer(1e-4).contains(Point(c["lon"], c["lat"]))]
print(f"subareas: {len(muni_ids)} | not in municipalities.json: {len(missing)}")
print(f"municipality admin_centres: {len(centres)} | outside polygon: {len(outside)} {outside}")

json.dump(province, open(OUT / "province.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
geo = {"type": "FeatureCollection", "features": [{
    "type": "Feature",
    "properties": {"osm_id": f"relation/{rel['id']}", "name": tags["official_name"], "istat": tags["ref:ISTAT"]},
    "geometry": mapping(polygon)}]}
json.dump(geo, open(OUT / "province_boundary.geojson", "w", encoding="utf-8"))
print("written:", OUT / "province.json", OUT / "province_boundary.geojson")
