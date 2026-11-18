"""Clean via_ferrata_routes.json -> via ferrata entities not already covered by the trails.

Input:  data/via_ferrata_routes.json  (Overpass export: 235 ways with geometry, 29 relations without members)
        data/clean/trails.json, data/clean/ways.json (to know what is already covered)
Output: data/clean/via_ferrata.json             -> one entity per via ferrata (flat attributes)
        data/clean/via_ferrata_geometry.geojson -> line of every via ferrata

A via ferrata is rebuilt by grouping the ways that are NOT already segments of a kept trail by their
normalized name. A group is kept only if it is verified as equipped by the tags (see via_ferrata.md).
"""
import json
import re
from collections import Counter, defaultdict

from shapely.geometry import LineString, mapping
from shapely.ops import linemerge

from route_common import BASE, haversine_m, line_length_m, load_province, province_rule, ROUNDTRIP_TOLERANCE_M

SRC = BASE / "data" / "via_ferrata_routes.json"
OUT = BASE / "data" / "clean"

# names that are not a via ferrata, or not usable
DROP_NAMES = {"emergency exit for ferrata"}
# different spellings / parts of the same via ferrata -> canonical normalized name
NAME_ALIASES = {
    "magnifici 4": "via ferrata i magnifici 4",
    "via ferrata crepa neigra - variante prima cima": "via ferrata crepa neigra",
}
SAC = {"strolling": 0, "hiking": 1, "mountain_hiking": 2, "demanding_mountain_hiking": 3,
       "alpine_hiking": 4, "demanding_alpine_hiking": 5, "difficult_alpine_hiking": 6}


def norm_name(n):
    k = re.sub(r"\s+", " ", n.strip().lower())
    return NAME_ALIASES.get(k, k)


def vfs_key(v):
    """Order of via_ferrata_scale values: '3-' < '3' < '3+'."""
    m = re.fullmatch(r"(\d)([+-]?)", v)
    return int(m.group(1)) + {"-": -0.3, "": 0, "+": 0.3}[m.group(2)] if m else -1


def is_equipped(ways, rel):
    return (any(w["tags"].get("highway") == "via_ferrata" for w in ways)
            or any("via_ferrata_scale" in w["tags"] for w in ways)
            or any(w["tags"].get("safety_rope") == "yes" for w in ways)
            or (rel is not None and rel["tags"].get("route") == "via_ferrata"))


def to_minutes(v):
    if not v:
        return None
    h, _, m = v.partition(":")
    return int(h) * 60 + int(m or 0)


elements = json.load(open(SRC, encoding="utf-8"))["elements"]
# ways already covered = segments of the kept trails, bike and foot routes
# (NOT data/clean/ways.json, which also contains the via ferrata ways written by a previous run)
covered = {wid for f in ("trails.json", "mtb.json", "foot_routes.json")
           for r in json.load(open(OUT / f, encoding="utf-8")) for wid in r["main_way_ids"]}
trail_ids = {t["osm_id"] for t in json.load(open(OUT / "trails.json", encoding="utf-8"))}
province = load_province()
stats = Counter()

# relations not already kept as trails, indexed by normalized name
rels = {}
for r in elements:
    if r["type"] != "relation":
        continue
    if f"relation/{r['id']}" in trail_ids:
        stats["relation_already_a_trail"] += 1
    elif r["tags"].get("name"):
        rels[norm_name(r["tags"]["name"])] = r
    else:
        stats["relation_dropped_no_name"] += 1

# group the uncovered ways by normalized name
groups, names = defaultdict(list), defaultdict(Counter)
for w in elements:
    if w["type"] != "way":
        continue
    if f"way/{w['id']}" in covered:
        stats["way_already_a_segment"] += 1
        continue
    n = w["tags"].get("name")
    if not n:
        stats["way_dropped_no_name"] += 1
        continue
    k = norm_name(n)
    if k in DROP_NAMES:
        stats["way_dropped_not_a_ferrata"] += 1
        continue
    groups[k].append(w)
    names[k][n] += 1

routes, features, dropped = [], [], []
for k, ws in sorted(groups.items()):
    rel = rels.pop(k, None)
    if not is_equipped(ws, rel):
        dropped.append((k, "not equipped"))
        continue
    lines = [LineString([(p["lon"], p["lat"]) for p in w["geometry"]]) for w in ws]
    merged = linemerge(lines)
    single = merged.geom_type == "LineString"
    if single:
        start, end, length_m = merged.coords[0], merged.coords[-1], line_length_m(merged)
    else:
        start, end = lines[0].coords[0], lines[-1].coords[-1]
        length_m = sum(line_length_m(x) for x in lines)
    geo = {"merged": merged, "start": start, "end": end}
    rule = province_rule(geo, province)
    if rule is None:
        dropped.append((k, f"outside province ({merged.intersection(province).length / merged.length:.0%} inside)"))
        continue

    rt = rel["tags"] if rel else {}
    vfs = [w["tags"]["via_ferrata_scale"] for w in ws if "via_ferrata_scale" in w["tags"]]
    if rt.get("via_ferrata_scale"):
        scale, scale_src = rt["via_ferrata_scale"], "relation"
    elif vfs:
        scale, scale_src = max(vfs, key=vfs_key), "ways_max"
    else:
        scale, scale_src = None, None
    sac = [SAC[w["tags"]["sac_scale"]] for w in ws if w["tags"].get("sac_scale") in SAC]
    # relation name first; else the most frequent spelling, ties broken by the longest (most complete) one
    name = rt.get("name") or max(names[k], key=lambda n: (names[k][n], len(n)))
    slug = re.sub(r"[^a-z0-9]+", "-", k).strip("-")
    # wikidata: relation first, else the value of the ways when they all agree
    way_qids = {w["tags"]["wikidata"] for w in ws if "wikidata" in w["tags"]}
    if rt.get("wikidata"):
        wikidata = rt["wikidata"]
    elif len(way_qids) == 1:
        wikidata = way_qids.pop()
    else:
        wikidata = None

    routes.append({
        "id": f"via_ferrata/{slug}",
        "osm_relation_id": f"relation/{rel['id']}" if rel else None,
        "kind": "via_ferrata",
        "name": name,
        "name_variants": sorted(names[k]) if len(names[k]) > 1 else None,
        "wikidata": wikidata,
        "via_ferrata_scale": scale,
        "via_ferrata_scale_source": scale_src,
        "sac_scale_max": max(sac) if sac else None,
        "duration_forward_min": to_minutes(rt.get("duration:forward")),
        "length_km_computed": round(length_m / 1000, 3),
        "roundtrip": (haversine_m(start, end) <= ROUNDTRIP_TOLERANCE_M) if single else None,
        "roundtrip_source": "geometry" if single else None,
        "province_rule": rule,
        "start": {"lat": round(start[1], 7), "lon": round(start[0], 7)},
        "end": {"lat": round(end[1], 7), "lon": round(end[0], 7)},
        "main_way_ids": [f"way/{w['id']}" for w in ws],
    })
    features.append({"type": "Feature",
                     "properties": {"id": routes[-1]["id"], "kind": "via_ferrata", "name": name},
                     "geometry": mapping(merged)})

for k, r in rels.items():
    dropped.append((k, "relation without matching ways (no geometry)"))

# ---------------- report ----------------
assert len({r["id"] for r in routes}) == len(routes)
print(dict(stats))
print(f"kept: {len(routes)}")
for r in routes:
    print(f"  {r['name'][:48]:48} ways={len(r['main_way_ids']):2} scale={r['via_ferrata_scale']!s:4} "
          f"({r['via_ferrata_scale_source']}) {r['length_km_computed']:6.3f} km  {r['province_rule']}"
          f"{'  ' + r['osm_relation_id'] if r['osm_relation_id'] else ''}")
print("dropped:")
for k, why in dropped:
    print(f"  {k}: {why}")

json.dump(routes, open(OUT / "via_ferrata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"type": "FeatureCollection", "features": features},
          open(OUT / "via_ferrata_geometry.geojson", "w", encoding="utf-8"), ensure_ascii=False)
print("written:", OUT / "via_ferrata.json", OUT / "via_ferrata_geometry.geojson")
