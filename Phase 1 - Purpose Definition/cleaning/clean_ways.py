"""Clean the way segments of all the kept routes into ONE file.

Sources (tags only, no geometry):
  data/ways.json               -> segments of the hiking trails (trails.json)
  data/full_stroller_mtb.json  -> segments of the bike routes (mtb.json) and foot routes (stroller.json)
Geometry for the length: the raw route files (trails.json, mtb.json, stroller.json) carry every way geometry.
Kept routes: data/clean/trails.json, mtb.json, foot_routes.json (main_way_ids).
Output: data/clean/ways.json  -> one entity per way segment used by at least one kept route
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
OUT = DATA / "clean"
# (segment source, raw route files with geometry, cleaned route files)
SOURCES = [
    ("ways.json", ["trails.json"], ["trails.json"]),
    ("full_stroller_mtb.json", ["mtb.json", "stroller.json"], ["mtb.json", "foot_routes.json"]),
    # via ferrata ways carry their own geometry (no relation members)
    ("via_ferrata_routes.json", ["via_ferrata_routes.json"], ["via_ferrata.json"]),
]

# ---------------- vocabularies ----------------
# non-standard / rare surface values -> standard OSM value
SURFACE_ALIASES = {
    "sterrato": "unpaved", "selciato": "sett", "cement": "concrete", "rocky": "rock",
    "unpaved,_cement": "unpaved", "gravel;ground": "gravel", "dirt;sand": "dirt",
    "metal grid": "metal_grid", "rubber": "paved",
}
PAVED = {
    "asphalt", "chipseal", "concrete", "concrete:plates", "concrete:lanes", "paved",
    "paving_stones", "sett", "cobblestone", "cobblestone:flattened", "cobblestone:flattened:lanes",
    "unhewn_cobblestone", "stone", "grass_paver", "metal", "metal_grid", "wood",
}
UNPAVED = {
    "unpaved", "ground", "earth", "dirt", "mud", "gravel", "fine_gravel", "compacted", "pebblestone",
    "grass", "rock", "bare_rock", "sand", "woodchips", "ice", "snow",
}
# surface_class inferred from highway when `surface` is missing
HIGHWAY_PAVED = {
    "primary", "primary_link", "secondary", "secondary_link", "tertiary", "trunk_link",
    "unclassified", "residential", "living_street", "service", "pedestrian", "footway", "cycleway",
}
HIGHWAY_UNPAVED = {"path", "via_ferrata", "bridleway"}

SMOOTHNESS = {"excellent": 1, "good": 2, "intermediate": 3, "medium": 3, "bad": 4,
              "very_bad": 5, "horrible": 6, "very_horrible": 7, "impassable": 8}
SAC = {"strolling": 0, "hiking": 1, "mountain_hiking": 2, "demanding_mountain_hiking": 3,
       "alpine_hiking": 4, "demanding_alpine_hiking": 5, "difficult_alpine_hiking": 6}
BIKE_YES = {"yes", "designated", "permissive", "mtb", "official"}
BIKE_NO = {"no", "dismount", "private"}


# ---------------- helpers ----------------
def haversine_m(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def surface_info(t):
    raw = t.get("surface")
    if raw:
        s = SURFACE_ALIASES.get(raw, raw)
        cls = "paved" if s in PAVED else "unpaved" if s in UNPAVED else None
        return s, cls, ("tag" if cls else None)
    hw = t.get("highway")
    if hw in HIGHWAY_PAVED:
        return None, "paved", "inferred_highway"
    if hw in HIGHWAY_UNPAVED:
        return None, "unpaved", "inferred_highway"
    if hw == "track":
        return None, ("paved" if t.get("tracktype") == "grade1" else "unpaved"), "inferred_tracktype"
    return None, None, None


def incline_pct(v):
    """Absolute slope in %. 'up'/'down'/'steep'/'yes' carry no number -> None. Degrees -> %."""
    if not v:
        return None
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)\s*(%|°)?", v.strip())
    if not m:
        return None
    x = abs(float(m.group(1)))
    if m.group(2) == "°":
        x = math.tan(math.radians(x)) * 100
    return round(x, 1)


def width_m(v):
    """Metres. Values > 20 are read as centimetres (60, 75, 54); 0 -> None."""
    if not v:
        return None
    m = re.match(r"(\d*\.?\d+)", v.replace(",", "."))
    if not m:
        return None
    x = float(m.group(1))
    if x == 0:
        return None
    return round(x / 100 if x > 20 else x, 2)


def sac_level(v):
    if not v:
        return None
    levels = [SAC[p] for p in v.split(";") if p in SAC]
    return max(levels) if levels else None


def mtb_level(v):
    if not v:
        return None
    levels = [int(m) for m in re.findall(r"\d", v)]
    return max(levels) if levels else None


def bicycle_allowed(v):
    return True if v in BIKE_YES else False if v in BIKE_NO else None


def build_way(el, t, length_m):
    aerialway = t.get("aerialway")
    if aerialway:
        # lift used as a stage of a bike route: no surface, no slope from tags
        surface, surface_class, surface_src = None, None, None
    else:
        surface, surface_class, surface_src = surface_info(t)
    return {
        "osm_id": f"way/{el['id']}",
        "highway": t.get("highway"),
        "aerialway": aerialway,
        "length_m": length_m,
        "surface": surface,
        "surface_class": surface_class,
        "surface_source": surface_src,
        "smoothness": SMOOTHNESS.get(t.get("smoothness")),
        "incline_pct": incline_pct(t.get("incline")),
        "width_m": width_m(t.get("width")),
        "sac_scale": sac_level(t.get("sac_scale")),
        "mtb_scale": mtb_level(t.get("mtb:scale")),
        "bicycle_allowed": bicycle_allowed(t.get("bicycle")),
        "wheelchair": t.get("wheelchair"),
        "stroller": t.get("stroller"),
        "via_ferrata_scale": t.get("via_ferrata_scale"),
    }


# ---------------- main ----------------
ways, stats, seen, all_used = [], Counter(), {}, set()
for seg_file, raw_files, clean_files in SOURCES:
    used = {int(wid.split("/")[1]) for f in clean_files for r in json.load(open(OUT / f, encoding="utf-8"))
            for wid in r["main_way_ids"]}
    all_used |= used

    lengths = {}
    for f in raw_files:
        for rel in json.load(open(DATA / f, encoding="utf-8"))["elements"]:
            # a way with its own geometry counts as a member of itself
            members = rel.get("members", []) or ([{**rel, "ref": rel["id"]}] if rel["type"] == "way" else [])
            for m in members:
                if m["type"] == "way" and len(m.get("geometry", [])) >= 2:
                    wid = int(str(m["ref"]).replace("_fullGeom", ""))
                    if wid in used and wid not in lengths:
                        g = m["geometry"]
                        lengths[wid] = round(sum(haversine_m(g[i], g[i + 1]) for i in range(len(g) - 1)), 1)

    for el in json.load(open(DATA / seg_file, encoding="utf-8"))["elements"]:
        t = el.get("tags", {})
        if el["id"] not in used:
            stats[f"{seg_file}: dropped_not_in_kept_routes"] += 1
            continue
        if el["id"] in seen:
            # same way already taken from the other source: tags must be identical
            assert seen[el["id"]] == t, f"way {el['id']}: tags differ between sources"
            stats[f"{seg_file}: duplicate_of_other_source"] += 1
            continue
        seen[el["id"]] = t
        stats[f"{seg_file}: kept"] += 1
        ways.append(build_way(el, t, lengths.get(el["id"])))

ways.sort(key=lambda w: int(w["osm_id"].split("/")[1]))

# ---------------- checks / report ----------------
assert len(ways) == len(all_used), f"{len(all_used) - len(ways)} route ways missing from the segment files"
assert all(w["length_m"] is not None for w in ways), "ways without length"
print(dict(stats))
print("total segments:", len(ways), "| aerialways:", Counter(w["aerialway"] for w in ways if w["aerialway"]))
tot = sum(w["length_m"] for w in ways if not w["aerialway"])
by = Counter()
for w in ways:
    if not w["aerialway"]:
        by[(w["surface_class"], w["surface_source"])] += w["length_m"]
print("surface_class by length (no aerialways):", {k: f"{v / tot:.1%}" for k, v in by.most_common()})
print("surface_source by count:", Counter(w["surface_source"] for w in ways))
for k in ["smoothness", "incline_pct", "width_m", "sac_scale", "mtb_scale", "bicycle_allowed", "wheelchair", "stroller"]:
    print(f"{k}: {sum(w[k] is not None for w in ways)} filled")
unmapped = Counter(w["surface"] for w in ways if w["surface"] and not w["surface_class"])
print("surface values without class:", dict(unmapped))

json.dump(ways, open(OUT / "ways.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written:", OUT / "ways.json")
