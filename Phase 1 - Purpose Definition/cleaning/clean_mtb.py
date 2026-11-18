"""Clean mtb.json (mountain-bike and cycling route relations).

Input:  data/mtb.json                       (Overpass export, 144 route relations with full geometry)
Output: data/clean/mtb.json                 -> one entity per bike route (flat attributes)
        data/clean/mtb_geometry.geojson     -> main line of every route
"""
import json
import re
from collections import Counter

from shapely.geometry import mapping

from route_common import (BASE, endpoints, guideposts, load_province, norm_operator,
                          province_rule, roundtrip, route_geometry, to_float, to_int_m)

SRC = BASE / "data" / "mtb.json"
OUT = BASE / "data" / "clean"
KIND_LABEL = {"mtb": "Percorso MTB", "bicycle": "Percorso ciclabile"}


def mtb_level(v):
    levels = [int(x) for x in re.findall(r"\d", v)] if v else []
    return max(levels) if levels else None


province = load_province()
routes, features, stats = [], [], Counter()

for el in json.load(open(SRC, encoding="utf-8"))["elements"]:
    t = el["tags"]
    kind = t["route"]
    if t.get("state") == "proposed":
        stats["dropped_proposed"] += 1
        continue
    geo = route_geometry(el)
    if geo is None:
        stats["dropped_no_geometry"] += 1
        continue
    rule = province_rule(geo, province)
    if rule is None:
        stats["dropped_outside_province"] += 1
        continue
    rt, rt_src = roundtrip(t, geo)

    ref = t.get("ref")
    if t.get("name") and t.get("stage"):
        name, name_src = f"{t['name']} – Tappa {t['stage']}", "name_stage"
    elif t.get("name"):
        name, name_src = t["name"], "name"
    elif ref and (t.get("from") or t.get("to")):
        name, name_src = f"{ref}: {t.get('from', '?')} – {t.get('to', '?')}", "ref_from_to"
    elif ref:
        name, name_src = f"{KIND_LABEL[kind]} {ref}", "ref"
    elif t.get("from") or t.get("to"):
        name, name_src = f"{t.get('from', '?')} – {t.get('to', '?')}", "from_to"
    else:
        name, name_src = f"{KIND_LABEL[kind]} {el['id']}", "osm_id"

    start, end = endpoints(geo)
    routes.append({
        "osm_id": f"relation/{el['id']}",
        "kind": kind,
        "ref": ref,
        "name": name,
        "name_source": name_src,
        "from": t.get("from"),
        "to": t.get("to"),
        "description": t.get("description"),
        "wikidata": t.get("wikidata"),
        "operator": norm_operator(t.get("operator")),
        "cai_scale_mtb": t.get("cai_scale:mtb"),
        "mtb_scale": mtb_level(t.get("mtb:scale")),
        "distance_km": to_float(t.get("distance") or t.get("length")),
        "distance_source": "distance" if t.get("distance") else "length" if t.get("length") else None,
        "length_km_computed": round(geo["length_m"] / 1000, 3),
        "ascent_m": to_int_m(t.get("ascent")),
        "descent_m": to_int_m(t.get("descent")),
        "roundtrip": rt,
        "roundtrip_source": rt_src,
        "province_rule": rule,
        "start": start,
        "end": end,
        "main_way_ids": [f"way/{wid}" for wid, _ in geo["ways"]],
        "guidepost_node_ids": guideposts(el),
    })
    features.append({"type": "Feature",
                     "properties": {"osm_id": f"relation/{el['id']}", "kind": kind, "ref": ref, "name": name},
                     "geometry": mapping(geo["merged"])})
    stats["kept"] += 1
    stats[f"kind_{kind}"] += 1
    stats[f"province_rule_{rule}"] += 1
    stats["merged_single_line" if geo["single"] else "not_merged"] += 1
    stats[f"roundtrip_{rt_src}"] += 1

# ---------------- checks / report ----------------
assert len({r["osm_id"] for r in routes}) == len(routes)
dup = [n for n, c in Counter(r["name"] for r in routes).items() if c > 1]
both = [r for r in routes if r["distance_km"]]
ratio = sorted(r["length_km_computed"] / r["distance_km"] for r in both)
print(dict(stats))
print("name sources:", Counter(r["name_source"] for r in routes))
print("duplicate names:", dup)
print("roundtrip:", Counter(r["roundtrip"] for r in routes))
print(f"computed/declared distance (n={len(ratio)}): median {ratio[len(ratio)//2]:.3f}, "
      f"within ±10%: {sum(0.9 <= x <= 1.1 for x in ratio) / len(ratio):.1%}")
print("operators:", Counter(o for r in routes for o in (r["operator"] or ["<none>"])).most_common())

json.dump(routes, open(OUT / "mtb.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"type": "FeatureCollection", "features": features},
          open(OUT / "mtb_geometry.geojson", "w", encoding="utf-8"), ensure_ascii=False)
print("written:", OUT / "mtb.json", OUT / "mtb_geometry.geojson")
