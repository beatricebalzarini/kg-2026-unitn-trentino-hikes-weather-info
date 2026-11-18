"""Helpers shared by the route cleaning scripts (mtb, stroller/foot).

Same rules as clean_trails.py: main ways, merged geometry, province filter, roundtrip, operator.
"""
import json
import math
import re
from pathlib import Path

from shapely.geometry import LineString, Point, shape
from shapely.ops import linemerge
from normalize import haversine_m, line_length_m, norm_operator  # noqa: F401  (re-exported)

BASE = Path(__file__).resolve().parent.parent
PROV = BASE / "data" / "clean" / "province_boundary.geojson"

MAIN_ROLES = {"", "forward", "backward"}
POST_ROLES = {"guidepost", "board"}
ROUNDTRIP_TOLERANCE_M = 50
MIN_INSIDE_RATIO = 0.5


def building_way_ids():
    """Ways tagged `building` (e.g. a hut building that is a member of a trail relation): they are not
    route segments. The route relations carry no way tags, so the tags come from the segment files."""
    out = set()
    for f in ("ways.json", "full_stroller_mtb.json"):
        for w in json.load(open(BASE / "data" / f, encoding="utf-8"))["elements"]:
            if w["type"] == "way" and "building" in w.get("tags", {}):
                out.add(w["id"])
    return out


BUILDINGS = None


def load_province():
    return shape(json.load(open(PROV, encoding="utf-8"))["features"][0]["geometry"])






def way_id(ref):
    return int(str(ref).replace("_fullGeom", ""))


def route_geometry(el):
    """Main ways (dedup by id, member order, buildings excluded) -> dict with merged geometry, endpoints, length."""
    global BUILDINGS
    if BUILDINGS is None:
        BUILDINGS = building_way_ids()
    seen, ways = set(), []
    for m in el["members"]:
        if m["type"] == "way" and m["role"] in MAIN_ROLES and len(m.get("geometry", [])) >= 2:
            wid = way_id(m["ref"])
            if wid in BUILDINGS:
                continue
            if wid not in seen:
                seen.add(wid)
                ways.append((wid, LineString([(p["lon"], p["lat"]) for p in m["geometry"]])))
    if not ways:
        return None
    merged = linemerge([w for _, w in ways])
    single = merged.geom_type == "LineString"
    if single:
        start, end, length_m = merged.coords[0], merged.coords[-1], line_length_m(merged)
    else:
        start, end = ways[0][1].coords[0], ways[-1][1].coords[-1]
        length_m = sum(line_length_m(w) for _, w in ways)
    return {"ways": ways, "merged": merged, "single": single, "start": start, "end": end, "length_m": length_m}


def province_rule(geo, province):
    """'endpoint' (starts/ends in Trentino), 'length_50' (>= 50% of the length inside) or None."""
    if province.contains(Point(geo["start"])) or province.contains(Point(geo["end"])):
        return "endpoint"
    if geo["merged"].intersection(province).length / geo["merged"].length >= MIN_INSIDE_RATIO:
        return "length_50"
    return None


def roundtrip(tags, geo):
    if tags.get("roundtrip") in ("yes", "no"):
        return tags["roundtrip"] == "yes", "tag"
    if geo["single"]:
        return haversine_m(geo["start"], geo["end"]) <= ROUNDTRIP_TOLERANCE_M, "geometry"
    return None, None


def to_float(v):
    return float(v.replace(",", ".")) if v is not None else None


def to_int_m(v):
    return int(v.replace(".", "")) if v is not None else None




def endpoints(geo):
    s, e = geo["start"], geo["end"]
    return {"lat": round(s[1], 7), "lon": round(s[0], 7)}, {"lat": round(e[1], 7), "lon": round(e[0], 7)}


def guideposts(el):
    return [f"node/{m['ref']}" for m in el["members"] if m["type"] == "node" and m["role"] in POST_ROLES]
