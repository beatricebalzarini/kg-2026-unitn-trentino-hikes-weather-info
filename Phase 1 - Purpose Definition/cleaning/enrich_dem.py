"""Fill the missing elevation values of the entity files with the Copernicus DEM GLO-30 (data/dem/).

Rule: an OSM tag always wins; the DEM only fills null fields, and every filled value is marked "dem" in its
`*_source` field. Where the tag exists the DEM value is computed only for comparison (data/entities/dem_validation.json).
The ER structure does not change: the only new attribute is Route.max_incline_pct (already in the ER model as a
derived attribute), plus provenance fields.

Route profile: each part of the route line is resampled every 30 m (in UTM 32N), the DEM is read with bilinear
interpolation, and:
  - ascent/descent: sum of the elevation changes larger than a 15 m threshold (hysteresis), to ignore DEM noise
    (threshold calibrated on the 542 routes with OSM ascent and descent: total climb median ratio DEM/OSM 1.01);
    measured from `start` to `end` of the geometry, which is not always the OSM from -> to direction;
  - ele_from/ele_to: DEM at the start/end point; ele_max/ele_min: highest/lowest sample;
  - max_incline_pct: slope of the steepest stretches = 95th percentile of |Δz| / distance over 100 m windows, on the
    profile smoothed with a 150 m moving median (the plain maximum is dominated by DEM artefacts on bridges,
    viaducts and steep side slopes); null for routes shorter than 100 m.
Points (huts, landmarks, facilities, stops): DEM at the point. Lakes and glaciers: median DEM inside the polygon.

Note: Copernicus GLO-30 is a surface model (DSM): in forests it can be some metres above the ground.
"""
import json
import math
from statistics import median

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.merge import merge
import shapely
from shapely.geometry import shape

from fetch_dem import ENT, tile_paths

STEP_M = 30
ASCENT_THRESHOLD_M = 15
SLOPE_WINDOW_M = 100
SLOPE_SMOOTH_SAMPLES = 5        # moving median over 5 samples = 150 m
SLOPE_PERCENTILE = 95

# ---------------- DEM ----------------
srcs = [rasterio.open(p) for p in tile_paths()]
DEM, TR = merge(srcs)
DEM = DEM[0].astype("float64")
for s in srcs:
    s.close()
X0, Y0, RES = TR.c, TR.f, TR.a
NODATA_BELOW = -1000          # Copernicus has no nodata value; anything below is treated as missing


def sample(lons, lats):
    """bilinear interpolation of the DEM at (lon, lat) arrays (pixel centres at x0 + (j + 0.5) * res)"""
    lons, lats = np.asarray(lons, float), np.asarray(lats, float)
    c = (lons - X0) / RES - 0.5
    r = (Y0 - lats) / RES - 0.5
    c0, r0 = np.floor(c).astype(int), np.floor(r).astype(int)
    c0 = np.clip(c0, 0, DEM.shape[1] - 2)
    r0 = np.clip(r0, 0, DEM.shape[0] - 2)
    dc, dr = c - c0, r - r0
    z = (DEM[r0, c0] * (1 - dc) * (1 - dr) + DEM[r0, c0 + 1] * dc * (1 - dr)
         + DEM[r0 + 1, c0] * (1 - dc) * dr + DEM[r0 + 1, c0 + 1] * dc * dr)
    z[z < NODATA_BELOW] = np.nan
    return z


to_utm = Transformer.from_crs(4326, 32632, always_xy=True).transform
to_wgs = Transformer.from_crs(32632, 4326, always_xy=True).transform


def project(g):
    """lon/lat geometry -> UTM 32N (metres)"""
    return shapely.transform(g, lambda c: np.column_stack(to_utm(c[:, 0], c[:, 1])))


def profile(line):
    """resample a lon/lat line every STEP_M metres -> (distances m, elevations m)"""
    u = project(line)
    n = max(2, int(math.ceil(u.length / STEP_M)) + 1)
    d = np.linspace(0, u.length, n)
    pts = [u.interpolate(x) for x in d]
    lon, lat = to_wgs(np.array([p.x for p in pts]), np.array([p.y for p in pts]))
    return d, sample(lon, lat)


def ascent_descent(z):
    up = down = 0.0
    ref = z[0]
    for v in z[1:]:
        if v - ref >= ASCENT_THRESHOLD_M:
            up += v - ref
            ref = v
        elif ref - v >= ASCENT_THRESHOLD_M:
            down += ref - v
            ref = v
    return up, down


def moving_median(z, k=SLOPE_SMOOTH_SAMPLES):
    if len(z) < k:
        return z
    zz = np.pad(z, k // 2, mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(zz, k), axis=1)


def window_slopes(d, z):
    """|slope| in % over all windows of SLOPE_WINDOW_M metres of the smoothed profile (empty if too short)"""
    if d[-1] < SLOPE_WINDOW_M:
        return np.array([])
    z = moving_median(z)
    j = np.searchsorted(d, d + SLOPE_WINDOW_M)
    ok = j < len(d)
    i, j = np.nonzero(ok)[0], j[ok]
    return np.abs(z[j] - z[i]) / (d[j] - d[i]) * 100


def fill(r, key, value, src_key=None):
    """fill r[key] only if null; return 'tag' or 'dem' (or None)"""
    if r.get(key) is not None:
        return "tag"
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    r[key] = int(round(value)) if key.endswith("_m") else round(value, 1)
    return "dem"


def reorder(r, after):
    """insert new keys after given existing keys, keeping the uniform order of the file"""
    out = {}
    for k, v in r.items():
        out[k] = v
        for new in after.get(k, []):
            out[new] = r.get(new)
    for k in r:
        out.setdefault(k, r[k])
    return out


_first = json.load(open(ENT / "routes.json", encoding="utf-8"))[0]
if "ascent_source" in _first:
    raise SystemExit("data/entities was already enriched: run build_entities.py first (or run_all.py), "
                     "otherwise DEM values would be read as OSM tags")

val = {"points": {}, "routes": {}, "polygons": {}, "ascent_pairs": []}

# ---------------- points ----------------
for f in ("hospitality", "facilities", "transport", "landmarks"):
    rows = json.load(open(ENT / f"{f}.json", encoding="utf-8"))
    polys = {}
    if f == "landmarks":
        polys = {ft["properties"]["id"]: shape(ft["geometry"])
                 for ft in json.load(open(ENT / "landmarks_geometry.geojson", encoding="utf-8"))["features"]}
    z = sample([r["lon"] for r in rows], [r["lat"] for r in rows])
    filled = 0
    for r, zp in zip(rows, z):
        if r["id"] in polys:                       # lake / glacier: median DEM inside the polygon
            g = polys[r["id"]]
            u = project(g)
            minx, miny, maxx, maxy = u.bounds
            xs, ys = np.meshgrid(np.arange(minx, maxx, STEP_M), np.arange(miny, maxy, STEP_M))
            xs, ys = xs.ravel(), ys.ravel()
            m = shapely.contains_xy(u, xs, ys)
            if not m.any():                        # polygon smaller than one grid step
                xs, ys, m = np.array([u.centroid.x]), np.array([u.centroid.y]), np.array([True])
            lon, lat = to_wgs(xs[m], ys[m])
            zp = float(np.nanmedian(sample(lon, lat)))
            val["polygons"].setdefault(r["category"], []).append((r["ele_m"], zp))
        elif r["ele_m"] is not None:
            val["points"].setdefault(f"{f}:{r['category']}", []).append((r["ele_m"], float(zp)))
        src = fill(r, "ele_m", None if math.isnan(zp) else float(zp))
        if src == "dem":
            filled += 1
        r["ele_source"] = src
    json.dump(rows, open(ENT / f"{f}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{f:12} ele_m filled from DEM: {filled} of {len(rows)}")

# ---------------- routes ----------------
geoms = {ft["properties"]["id"]: shape(ft["geometry"])
         for ft in json.load(open(ENT / "routes_geometry.geojson", encoding="utf-8"))["features"]}
routes = json.load(open(ENT / "routes.json", encoding="utf-8"))
stats = {k: 0 for k in ("ascent_m", "descent_m", "ele_from_m", "ele_to_m", "ele_max_m", "ele_min_m", "max_incline_pct")}
out = []
for r in routes:
    g = geoms[r["id"]]
    parts = list(g.geoms) if g.geom_type == "MultiLineString" else [g]
    up = down = 0.0
    zs, slopes = [], []
    for p in parts:
        d, z = profile(p)
        z = np.where(np.isnan(z), np.nanmean(z), z)
        a, b = ascent_descent(z)
        up, down = up + a, down + b
        zs.append(z)
        slopes.append(window_slopes(d, z))
    allz = np.concatenate(zs)
    z_start, z_end = sample([r["start"]["lon"], r["end"]["lon"]], [r["start"]["lat"], r["end"]["lat"]])
    dem = {"ascent_m": up, "descent_m": down, "ele_from_m": float(z_start), "ele_to_m": float(z_end),
           "ele_max_m": float(allz.max()), "ele_min_m": float(allz.min())}
    for k in ("ascent_m", "ele_max_m"):
        if r[k] is not None:
            val["routes"].setdefault(k, []).append((r[k], dem[k]))
    if r["ascent_m"] is not None and r["descent_m"] is not None:
        val["ascent_pairs"].append((r["ascent_m"], r["descent_m"], up, down))
    r["ascent_source"] = fill(r, "ascent_m", dem["ascent_m"])
    r["descent_source"] = fill(r, "descent_m", dem["descent_m"])
    ele_srcs = {fill(r, k, dem[k]) for k in ("ele_from_m", "ele_to_m", "ele_max_m", "ele_min_m")} - {None}
    r["ele_source"] = "tag+dem" if ele_srcs == {"tag", "dem"} else (ele_srcs.pop() if ele_srcs else None)
    slopes = np.concatenate(slopes)
    r["max_incline_pct"] = round(float(np.percentile(slopes, SLOPE_PERCENTILE)), 1) if len(slopes) else None
    r["max_incline_source"] = "dem" if len(slopes) else None
    for k in stats:
        stats[k] += r.get(k) is not None
    out.append(reorder(r, {"descent_m": ["ascent_source", "descent_source"],
                           "ele_source": ["max_incline_pct", "max_incline_source"]}))
json.dump(out, open(ENT / "routes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("routes filled now:", {k: f"{v}/{len(out)}" for k, v in stats.items()})


# ---------------- validation (DEM vs OSM tags) ----------------
def summary(pairs):
    diff = [z - t for t, z in pairs]
    return {"n": len(pairs), "median_diff_m": round(median(diff), 1),
            "median_abs_diff_m": round(median(abs(x) for x in diff), 1),
            "within_25m_pct": round(100 * sum(abs(x) <= 25 for x in diff) / len(diff), 1)}


report = {"points": {k: summary(v) for k, v in sorted(val["points"].items()) if len(v) >= 10},
          "polygons": {k: summary([(t, z) for t, z in v if t is not None]) for k, v in val["polygons"].items()
                       if sum(t is not None for t, _ in v) >= 5},
          "routes": {}}
asc = val["routes"]["ascent_m"]
ratio = sorted(z / t for t, z in asc if t > 0)
report["routes"]["ascent_m"] = {"n": len(asc), "median_ratio_dem_tag": round(median(ratio), 3),
                                "within_20pct": round(100 * sum(0.8 <= x <= 1.2 for x in ratio) / len(ratio), 1)}
report["routes"]["ele_max_m"] = summary(val["routes"]["ele_max_m"])
# orientation check: OSM ascent/descent refer to from->to, the DEM profile to the geometry start->end
pairs = [(ta, td, da, dd) for ta, td, da, dd in val["ascent_pairs"] if ta > 0 and td > 0]
same = [0.8 <= da / ta <= 1.2 and 0.8 <= dd / td <= 1.2 for ta, td, da, dd in pairs]
swap = [0.8 <= dd / ta <= 1.2 and 0.8 <= da / td <= 1.2 for ta, td, da, dd in pairs]
tot = sorted((da + dd) / (ta + td) for ta, td, da, dd in pairs)
report["routes"]["orientation_check"] = {
    "n": len(pairs), "same_direction_within_20pct": round(100 * sum(same) / len(pairs), 1),
    "opposite_direction_within_20pct": round(100 * sum(swap) / len(pairs), 1),
    "total_climb_up_plus_down_within_20pct": round(100 * sum(0.8 <= x <= 1.2 for x in tot) / len(tot), 1),
    "total_climb_median_ratio": round(median(tot), 3)}
report["parameters"] = {"step_m": STEP_M, "ascent_threshold_m": ASCENT_THRESHOLD_M, "slope_window_m": SLOPE_WINDOW_M,
                        "slope_smoothing_m": SLOPE_SMOOTH_SAMPLES * STEP_M, "slope_percentile": SLOPE_PERCENTILE,
                        "dem": "Copernicus DEM GLO-30", "tiles": [p.name for p in tile_paths()]}
json.dump(report, open(ENT / "dem_validation.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(report, indent=1))
