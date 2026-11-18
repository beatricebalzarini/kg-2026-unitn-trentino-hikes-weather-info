"""Remove the duplicates BETWEEN cleaned files: the same real object mapped twice in OSM with different ids
(e.g. a hut as a building in huts.json and as a point in food_drink.json).

Runs last (after all clean_*.py). It rewrites the cleaned files in place:
the duplicate is removed from the secondary file, and the kept entity in the primary file gets
`duplicates` = [{"osm_id", "file"}] plus the useful fields it was missing.

Rule: same normalized name + within 100 m (for lakes/glaciers: within 100 m of the polygon)
+ a compatible pair of files (below). Other same-name neighbours (a guidepost at a hut, a bus stop named
after a pass, a castle with a restaurant inside) are different objects and are NOT duplicates.

Usage: python dedup_cross_files.py [--dry-run]
"""
import json
import re
import sys
from collections import Counter

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from route_common import haversine_m
from poi_common import CLEAN

MAX_DISTANCE_M = 100
# (primary file, secondary file, condition on the secondary entity, fields copied to the primary when missing)
PAIRS = [
    ("huts", "food_drink", None, ["cuisine", "opening_hours", "phone", "email", "website", "wikidata"]),
    ("accommodations", "food_drink", None, ["cuisine", "opening_hours", "phone", "email", "website", "wikidata"]),
    ("huts", "accommodations", None, ["phone", "email", "website", "wikidata", "opening_hours"]),
    ("landmarks", "cultural_landmarks", {"attraction", "viewpoint"}, ["wikidata"]),
    ("lakes", "cultural_landmarks", {"attraction", "viewpoint"}, ["wikidata"]),
    ("glaciers", "cultural_landmarks", {"attraction", "viewpoint"}, ["wikidata"]),
]
REAL_NAME = {"name", "osm"}       # generated labels are never used to match


def norm(n):
    return re.sub(r"\s+", " ", n.strip().lower())


def name_of(r):
    return r.get("name_osm") or r["name"]


dry = "--dry-run" in sys.argv
data = {f: json.load(open(CLEAN / f"{f}.json", encoding="utf-8"))
        for f in {p for pair in PAIRS for p in pair[:2]}}
polys = {f: {ft["properties"]["osm_id"]: shape(ft["geometry"])
             for ft in json.load(open(CLEAN / f"{f}_geometry.geojson", encoding="utf-8"))["features"]}
         for f in ("lakes", "glaciers")}

removed = {f: set() for f in data}
found, stats = [], Counter()
for prim, sec, cond, fields in PAIRS:
    cands = [r for r in data[sec] if r.get("name_source") in REAL_NAME and r["osm_id"] not in removed[sec]
             and (cond is None or r.get("category") in cond)]
    by_name = {}
    for r in cands:
        by_name.setdefault(norm(name_of(r)), []).append(r)
    for p in data[prim]:
        if p.get("name_source") not in REAL_NAME or p["osm_id"] in removed[prim]:
            continue
        for s in by_name.get(norm(name_of(p)), []):
            if s["osm_id"] in removed[sec]:
                continue
            if prim in polys:   # distance from the polygon (degrees -> metres, approx. at this latitude)
                d = polys[prim][p["osm_id"]].distance(Point(s["lon"], s["lat"])) * 111_000
            else:
                d = haversine_m((p["lon"], p["lat"]), (s["lon"], s["lat"]))
            if d > MAX_DISTANCE_M:
                continue
            found.append((prim, sec, name_of(p), p["osm_id"], s["osm_id"], s.get("category"), round(d)))
            removed[sec].add(s["osm_id"])
            p.setdefault("duplicates", [])
            p["duplicates"] = (p["duplicates"] or []) + [{"osm_id": s["osm_id"], "file": f"{sec}.json"}]
            for k in fields:
                if p.get(k) in (None, []) and s.get(k) not in (None, []):
                    p[k] = s[k]
                    stats[f"filled {prim}.{k}"] += 1
            if sec == "food_drink" and p.get("food_service") is not True:
                p["food_service"], p["food_service_source"] = True, "duplicate_food_drink"
                stats[f"filled {prim}.food_service"] += 1
            stats[f"{prim} <- {sec}"] += 1

print("duplicates found:", sum(1 for _ in found))
for x in found:
    print("  ", x)
print(dict(stats))
if dry:
    print("dry run: nothing written")
    sys.exit()

for f, rows in data.items():
    rows = [r for r in rows if r["osm_id"] not in removed[f]]
    for r in rows:
        r.setdefault("duplicates", None)
    json.dump(rows, open(CLEAN / f"{f}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"written {f}.json: {len(rows)} (removed {len(removed[f])})")
