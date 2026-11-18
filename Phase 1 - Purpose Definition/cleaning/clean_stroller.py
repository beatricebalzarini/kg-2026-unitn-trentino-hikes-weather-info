"""Clean stroller.json (13 route=foot relations).

Despite the file name, nothing in the data says these routes are stroller-friendly (see foot_routes.md):
they are kept as generic walking routes, kind = "foot".

Input:  data/stroller.json
Output: data/clean/foot_routes.json             -> one entity per walking route (flat attributes)
        data/clean/foot_routes_geometry.geojson -> main line of every route
"""
import json
from collections import Counter

from shapely.geometry import mapping

from route_common import (BASE, endpoints, guideposts, load_province, norm_operator,
                          province_rule, roundtrip, route_geometry)

SRC = BASE / "data" / "stroller.json"
OUT = BASE / "data" / "clean"

province = load_province()
routes, features, stats = [], [], Counter()

for el in json.load(open(SRC, encoding="utf-8"))["elements"]:
    t = el["tags"]
    geo = route_geometry(el)
    if geo is None:
        stats["dropped_no_geometry"] += 1
        print("dropped (no geometry):", el["id"], t.get("name"))
        continue
    rule = province_rule(geo, province)
    if rule is None:
        stats["dropped_outside_province"] += 1
        continue
    rt, rt_src = roundtrip(t, geo)

    ref = t.get("ref")
    if t.get("name"):
        name, name_src = t["name"], "name"
    elif ref:
        name, name_src = f"Percorso {ref}", "ref"
    elif t.get("from") or t.get("to"):
        name, name_src = f"{t.get('from', '?')} – {t.get('to', '?')}", "from_to"
    else:
        name, name_src = f"Percorso a piedi {el['id']}", "osm_id"

    start, end = endpoints(geo)
    routes.append({
        "osm_id": f"relation/{el['id']}",
        "kind": "foot",
        "ref": ref,
        "name": name,
        "name_source": name_src,
        "from": t.get("from"),
        "to": t.get("to"),
        "description": t.get("description"),
        "wikidata": t.get("wikidata"),
        "operator": norm_operator(t.get("operator")),
        "length_km_computed": round(geo["length_m"] / 1000, 3),
        "roundtrip": rt,
        "roundtrip_source": rt_src,
        "province_rule": rule,
        "start": start,
        "end": end,
        "main_way_ids": [f"way/{wid}" for wid, _ in geo["ways"]],
        "guidepost_node_ids": guideposts(el),
    })
    features.append({"type": "Feature",
                     "properties": {"osm_id": f"relation/{el['id']}", "kind": "foot", "ref": ref, "name": name},
                     "geometry": mapping(geo["merged"])})
    stats["kept"] += 1
    stats[f"province_rule_{rule}"] += 1
    stats["merged_single_line" if geo["single"] else "not_merged"] += 1
    stats[f"roundtrip_{rt_src}"] += 1

assert len({r["osm_id"] for r in routes}) == len(routes)
print(dict(stats))
for r in routes:
    print(f"  {r['osm_id']:>9}  {r['length_km_computed']:7.3f} km  roundtrip={r['roundtrip']!s:5} "
          f"({r['roundtrip_source']})  {r['name']}")

json.dump(routes, open(OUT / "foot_routes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"type": "FeatureCollection", "features": features},
          open(OUT / "foot_routes_geometry.geojson", "w", encoding="utf-8"), ensure_ascii=False)
print("written:", OUT / "foot_routes.json", OUT / "foot_routes_geometry.geojson")
