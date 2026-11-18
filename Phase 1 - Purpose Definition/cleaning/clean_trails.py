"""Clean trails.json (hiking route relations).

Input:  data/trails.json                        (Overpass export, 1657 route relations with full geometry)
        data/clean/province_boundary.geojson    (from clean_province_boundaries.py)
Output: data/clean/trails.json                  -> one entity per trail (flat attributes)
        data/clean/trails_geometry.geojson      -> main line of every trail (for spatial joins)
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

from shapely.geometry import LineString, Point, mapping, shape
from shapely.ops import linemerge

from normalize import haversine_m, line_length_m, norm_operator

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "trails.json"
PROV = BASE / "data" / "clean" / "province_boundary.geojson"
OUT = BASE / "data" / "clean"

MAIN_ROLES = {"", "forward", "backward"}      # ways that form the route itself
POST_ROLES = {"guidepost", "board"}           # signposts along the route
ROUNDTRIP_TOLERANCE_M = 50
MIN_INSIDE_RATIO = 0.5                        # share of the trail length inside the province


# ---------------- helpers ----------------




def to_float(v):
    return float(v) if v is not None else None


def to_int_m(v):
    """Metres as integer. '1.692' uses '.' as thousands separator (no ascent has decimals)."""
    if v is None:
        return None
    return int(v.replace(".", ""))


def to_minutes(v):
    """'HH:MM' -> minutes; a bare number is read as hours (one case: '5')."""
    if v is None:
        return None
    if ":" in v:
        h, m = v.split(":")
        return int(h) * 60 + int(m)
    return int(v) * 60




def split_cai(scale):
    """'EEA:PD' -> ('EEA', 'PD'); 'E' -> ('E', None)."""
    if scale is None:
        return None, None
    base, _, grade = scale.partition(":")
    return base, (grade or None)


# ---------------- main ----------------
province = shape(json.load(open(PROV, encoding="utf-8"))["features"][0]["geometry"])
elements = json.load(open(SRC, encoding="utf-8"))["elements"]
from route_common import building_way_ids  # noqa: E402  (shared rule with the bike/foot routes)
BUILDINGS = building_way_ids()

trails, features = [], []
stats = Counter()

for el in elements:
    t = el["tags"]
    if t.get("type") == "superroute":
        stats["dropped_superroute"] += 1
        continue

    # main ways, deduplicated by way id (keeps member order); buildings (e.g. a hut) are not segments
    seen, ways = set(), []
    for m in el["members"]:
        if m["type"] == "way" and m["role"] in MAIN_ROLES and len(m.get("geometry", [])) >= 2:
            wid = int(m["ref"].replace("_fullGeom", ""))
            if wid in BUILDINGS:
                stats["building_ways_excluded"] += 1
                continue
            if wid not in seen:
                seen.add(wid)
                ways.append((wid, LineString([(p["lon"], p["lat"]) for p in m["geometry"]])))
    if not ways:
        stats["dropped_no_geometry"] += 1
        continue

    merged = linemerge([w for _, w in ways])
    single = merged.geom_type == "LineString"
    if single:
        start, end = merged.coords[0], merged.coords[-1]
        length_m = line_length_m(merged)
    else:
        start, end = ways[0][1].coords[0], ways[-1][1].coords[-1]   # member order
        length_m = sum(line_length_m(w) for _, w in ways)

    # province filter: kept if (1) it starts or ends in Trentino, OR (2) at least 50% of its length is inside
    if province.contains(Point(start)) or province.contains(Point(end)):
        province_rule = "endpoint"
    elif merged.intersection(province).length / merged.length >= MIN_INSIDE_RATIO:
        province_rule = "length_50"
    else:
        stats["dropped_outside_province"] += 1
        continue
    stats[f"province_rule_{province_rule}"] += 1

    # roundtrip: tag first, else geometry only when the ways merge into one line
    if t.get("roundtrip") in ("yes", "no"):
        roundtrip, rt_src = t["roundtrip"] == "yes", "tag"
    elif single:
        roundtrip, rt_src = haversine_m(start, end) <= ROUNDTRIP_TOLERANCE_M, "geometry"
    else:
        roundtrip, rt_src = None, None

    # label
    ref = t.get("ref")
    if t.get("name"):
        name, name_src = t["name"], "name"
    elif ref and (t.get("from") or t.get("to")):
        name, name_src = f"{ref}: {t.get('from', '?')} – {t.get('to', '?')}", "ref_from_to"
    elif ref:
        name, name_src = f"Sentiero {ref}", "ref"
    elif t.get("from") or t.get("to"):
        name, name_src = f"{t.get('from', '?')} – {t.get('to', '?')}", "from_to"
    else:
        name, name_src = f"Trail {el['id']}", "osm_id"

    cai, ferrata_grade = split_cai(t.get("cai_scale"))

    trail = {
        "osm_id": f"relation/{el['id']}",
        "ref": ref,
        "reg_ref": t.get("reg_ref"),
        "name": name,
        "name_source": name_src,
        "from": t.get("from"),
        "to": t.get("to"),
        "description": t.get("description") or t.get("description:it"),
        "wikidata": t.get("wikidata"),
        "operator": norm_operator(t.get("operator")),
        "cai_scale": cai,
        "ferrata_grade": ferrata_grade,
        "via_ferrata_scale": t.get("via_ferrata_scale"),
        "distance_km": to_float(t.get("distance")),
        "length_km_computed": round(length_m / 1000, 3),
        "duration_forward_min": to_minutes(t.get("duration:forward")),
        "duration_backward_min": to_minutes(t.get("duration:backward")),
        "ascent_m": to_int_m(t.get("ascent")),
        "descent_m": to_int_m(t.get("descent")),
        "ele_from_m": to_int_m(t.get("ele:from")),
        "ele_to_m": to_int_m(t.get("ele:to")),
        "ele_max_m": to_int_m(t.get("ele:max")),
        "ele_min_m": to_int_m(t.get("ele:min")),
        "roundtrip": roundtrip,
        "roundtrip_source": rt_src,
        "province_rule": province_rule,
        "start": {"lat": round(start[1], 7), "lon": round(start[0], 7)},
        "end": {"lat": round(end[1], 7), "lon": round(end[0], 7)},
        "main_way_ids": [f"way/{wid}" for wid, _ in ways],
        "guidepost_node_ids": [f"node/{m['ref']}" for m in el["members"]
                               if m["type"] == "node" and m["role"] in POST_ROLES],
    }
    trails.append(trail)
    features.append({
        "type": "Feature",
        "properties": {"osm_id": f"relation/{el['id']}", "ref": ref, "name": name},
        "geometry": mapping(merged),
    })
    stats["kept"] += 1
    stats["merged_single_line" if single else "not_merged"] += 1
    stats[f"roundtrip_{rt_src}"] += 1

# ---------------- checks / report ----------------
assert len({t["osm_id"] for t in trails}) == len(trails)
both = [t for t in trails if t["distance_km"]]
ratio = sorted(t["length_km_computed"] / t["distance_km"] for t in both if t["distance_km"] > 0)
print(dict(stats))
print(f"name sources: {Counter(t['name_source'] for t in trails)}")
print(f"roundtrip: {Counter(t['roundtrip'] for t in trails)}")
print(f"computed/declared distance (n={len(ratio)}): median {ratio[len(ratio)//2]:.3f}, "
      f"within ±10%: {sum(0.9 <= r <= 1.1 for r in ratio) / len(ratio):.1%}")
print(f"operators: {Counter(o for t in trails for o in (t['operator'] or ['<none>'])).most_common(8)}")

json.dump(trails, open(OUT / "trails.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"type": "FeatureCollection", "features": features},
          open(OUT / "trails_geometry.geojson", "w", encoding="utf-8"), ensure_ascii=False)
print("written:", OUT / "trails.json", OUT / "trails_geometry.geojson")
