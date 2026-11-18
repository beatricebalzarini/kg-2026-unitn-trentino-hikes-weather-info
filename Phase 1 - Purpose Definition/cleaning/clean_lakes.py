"""Clean lakes_geom.json -> lakes.json + glaciers.json (+ polygon GeoJSONs).

Input:  data/lakes_geom.json (Overpass export with full geometry, 227 ways/relations)
        (data/lakes.json, the first export with only `center`, is no longer used)
Output: data/clean/lakes.json, data/clean/glaciers.json
        data/clean/lakes_geometry.geojson, data/clean/glaciers_geometry.geojson
"""
import json
from collections import Counter, defaultdict

from pyproj import Geod
from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

from route_common import BASE, haversine_m
from poi_common import CLEAN, Municipalities, ele_m, osm_key

SRC = BASE / "data" / "lakes_geom.json"
BASIN_MAX_DISTANCE_M = 1000      # same name closer than this -> basins/parts of the same object
GEOD = Geod(ellps="WGS84")


def area_km2(g):
    return abs(GEOD.geometry_area_perimeter(g)[0]) / 1e6


def polygon(el):
    if el["type"] == "way":
        return Polygon([(p["lon"], p["lat"]) for p in el["geometry"]])
    rings = lambda role: [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
                          for m in el["members"] if m["role"] == role and len(m.get("geometry", [])) >= 2]
    outer = unary_union(list(polygonize(unary_union(rings("outer")))))
    inner = rings("inner")
    return outer.difference(unary_union(list(polygonize(unary_union(inner))))) if inner else outer


def yes_no(v):
    return True if v == "yes" else False if v == "no" else None


munis = Municipalities()
mtree = STRtree(munis.geoms)
out = {"water": [], "glacier": []}
geoms = {"water": [], "glacier": []}
stats = Counter()

for el in json.load(open(SRC, encoding="utf-8"))["elements"]:
    t = el["tags"]
    g = polygon(el)
    assert g.is_valid and not g.is_empty, f"invalid polygon {osm_key(el)}"
    inside = g.intersection(munis.province)
    # province rule (a), user decision: kept if any part of the polygon is in Trentino
    if inside.is_empty:
        stats["dropped_outside_province"] += 1
        continue
    # point always inside the polygon, taken in its Trentino part (for border objects like Lake Garda)
    rp = inside.representative_point()
    # all the Trentino municipalities touched by the polygon, largest overlap first
    touched = []
    for i in mtree.query(g):
        a = munis.geoms[i].intersection(g)
        if not a.is_empty and a.area > 0:
            touched.append((a.area, munis.props[i]["istat"]))
    row = {
        "osm_id": osm_key(el),
        "name": t["name"],
        "ele_m": ele_m(t.get("ele") or t.get("elevation")),
        "ele_source": "ele" if t.get("ele") else "elevation" if t.get("elevation") else None,
        "area_km2": round(area_km2(g), 4),
        "area_inside_pct": round(100 * inside.area / g.area, 1),
        "lat": round(rp.y, 7),
        "lon": round(rp.x, 7),
        "municipalities_istat": [m for _, m in sorted(touched, reverse=True)],
        "wikidata": t.get("wikidata"),
    }
    if t["natural"] == "water":
        row.update({
            "swimming": yes_no(t.get("swimming")),
            "fishing": t.get("fishing") if t.get("fishing") in ("yes", "no", "license") else None,
            "boat": yes_no(t.get("boat")),
        })
    out[t["natural"]].append(row)
    geoms[t["natural"]].append((row["osm_id"], g))
    stats[f"{t['natural']}:kept"] += 1
    if row["area_inside_pct"] < 100:
        stats[f"{t['natural']}:partly_outside"] += 1

# ---------------- same names: different objects, disambiguated (user decision) ----------------
muni_name = {m["istat"]: m["name"] for m in json.load(open(CLEAN / "municipalities.json", encoding="utf-8"))}
renamed = []
for k, rows in out.items():
    for r in rows:
        r["name_osm"] = r["name"]
    g = defaultdict(list)
    for r in rows:
        g[r["name"]].append(r)
    for n, v in g.items():
        if len(v) < 2:
            continue
        d = max(haversine_m((a["lon"], a["lat"]), (b["lon"], b["lat"])) for a in v for b in v)
        if d < BASIN_MAX_DISTANCE_M:
            word = "basin" if k == "water" else "part"
            for i, r in enumerate(sorted(v, key=lambda r: -r["lat"]), 1):     # numbered north -> south
                r["name"], r["name_source"] = f"{n} – {word} {i}", f"osm_{word}"
        else:
            by_muni = defaultdict(list)
            for r in v:
                by_muni[muni_name[r["municipalities_istat"][0]]].append(r)
            for m, rs in by_muni.items():
                for i, r in enumerate(sorted(rs, key=lambda r: -r["lat"]), 1):
                    suffix = f" {i}" if len(rs) > 1 else ""
                    r["name"], r["name_source"] = f"{n} ({m}{suffix})", "osm_municipality"
        renamed.append((n, len(v), round(d), sorted(r["name"] for r in v)))
    for r in rows:
        r.setdefault("name_source", "osm")

# ---------------- checks / report ----------------
print(dict(stats))
for k, rows in out.items():
    assert len({r["osm_id"] for r in rows}) == len(rows)
    assert len({r["name"] for r in rows}) == len(rows), f"{k}: names still not unique"
    assert all(r["municipalities_istat"] for r in rows)
    print(k, len(rows), "| ele:", sum(r["ele_m"] is not None for r in rows),
          "| wikidata:", sum(bool(r["wikidata"]) for r in rows),
          "| area km2 total:", round(sum(r["area_km2"] for r in rows), 1))
    print("  partly outside Trentino:",
          sorted(((r["area_inside_pct"], r["name"]) for r in rows if r["area_inside_pct"] < 100))[:20])
    print("  more than one municipality:", sum(len(r["municipalities_istat"]) > 1 for r in rows),
          "| max:", max((len(r["municipalities_istat"]), r["name"]) for r in rows))
print("renamed (osm name, n, max distance m, new names):")
for x in renamed:
    print("  ", x)

order = ["osm_id", "name", "name_osm", "name_source"]
for k, f in [("water", "lakes"), ("glacier", "glaciers")]:
    rows = [{**{c: r[c] for c in order}, **{c: v for c, v in r.items() if c not in order}} for r in out[k]]
    json.dump(sorted(rows, key=lambda r: r["osm_id"]), open(CLEAN / f"{f}.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    names = {r["osm_id"]: r["name"] for r in rows}
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"osm_id": i, "name": names[i]}, "geometry": mapping(g)}
        for i, g in sorted(geoms[k])]}
    json.dump(fc, open(CLEAN / f"{f}_geometry.geojson", "w", encoding="utf-8"), ensure_ascii=False)
    print("written:", CLEAN / f"{f}.json", len(rows), "+", f"{f}_geometry.geojson")
