"""Clean public_transportation.json -> transport stops + aerialway lines.

Input:  data/public_transportation.json (Overpass export, 4948 nodes/ways/relations)
        data/clean/_pending_bus_shelters.json (bus shelters parked by clean_huts_landmarks.py)
Output: data/clean/transport_stops.json  -> bus stops/stations, train stations, funicular and lift stations
        data/clean/aerialways.json       -> lift lines (chair lifts, gondolas, cable cars)
"""
import json
import re
from collections import Counter, defaultdict

from shapely.geometry import Point
from shapely.strtree import STRtree

from route_common import BASE, haversine_m
from poi_common import CLEAN, Municipalities, ele_m, osm_key, position

SRC = BASE / "data" / "public_transportation.json"
SHELTER_MATCH_M = 30          # a pending bus shelter belongs to the nearest bus stop within this distance
MERGE_STOPS_M = 100           # same name + same mode within this distance -> one stop (user decision)
LIFT_LINES = {"chair_lift", "gondola", "cable_car", "mixed_lift", "drag_lift", "t-bar", "platter", "magic_carpet", "yes"}
LABELS = {("bus", "stop"): "Fermata bus", ("bus", "station"): "Autostazione", ("train", "station"): "Stazione",
          ("funicular", "station"): "Funicolare", ("aerialway", "station"): "Stazione impianto"}


def norm_operator(op):
    if not op:
        return None
    out = []
    for p in (x.strip() for x in re.split(r"[;,]", op)):
        low = p.lower()
        if not p:
            continue
        if "trentino trasporti" in low or "ttesercizio" in low:
            p = "Trentino Trasporti"
        elif "dolomitibus" in low:
            p = "DolomitiBus"
        elif "rete ferroviaria italiana" in low or low == "rfi":
            p = "RFI"
        elif low.startswith("linea "):          # a bus line, not an operator
            continue
        if p not in out:
            out.append(p)
    return out or None


def duration_min(v):
    """'7' -> 7.0 ; '7:10' (min:sec) -> 7.17"""
    if not v:
        return None
    m = re.fullmatch(r"\s*(\d+)(?::(\d{1,2}))?\s*", v)
    return round(int(m.group(1)) + (int(m.group(2) or 0) / 60), 2) if m else None


def classify(t):
    """-> ('stop', mode, kind) | ('line', type, None) | ('drop', reason, None)"""
    aw = t.get("aerialway")
    if aw == "station":
        return "stop", "aerialway", "station"
    if aw in LIFT_LINES:
        return "line", aw, None
    if aw:
        return "drop", f"aerialway={aw}", None
    if t.get("station") == "funicular":
        return "stop", "funicular", "station"
    if t.get("railway") in ("station", "halt") or t.get("station") == "train" or t.get("train") == "yes":
        return "stop", "train", "station"
    if t.get("amenity") == "bus_station":
        return "stop", "bus", "station"
    if t.get("public_transport") == "station":
        return "stop", "bus", "station"
    if t.get("highway", "").startswith("bus_stop") or t.get("public_transport") in ("platform", "stop_position"):
        return "stop", "bus", "stop"
    return "drop", "other", None


munis = Municipalities()
stops, lines, stats, dropped = [], [], Counter(), Counter()

for el in json.load(open(SRC, encoding="utf-8"))["elements"]:
    t = el["tags"]
    lat, lon = position(el)
    if not munis.province.contains(Point(lon, lat)):
        stats["dropped_outside_province"] += 1
        continue
    what, a, b = classify(t)
    if what == "drop":
        dropped[a] += 1
        continue
    muni = munis.find(lat, lon)
    base = {"osm_id": osm_key(el), "name": t.get("name"), "lat": round(lat, 7), "lon": round(lon, 7),
            "municipality_istat": muni["istat"], "muni_name": muni["name"],
            "operator": norm_operator(t.get("operator")), "wikidata": t.get("wikidata")}
    if what == "stop":
        shelter = {"yes": True, "separate": True, "no": False}.get(t.get("shelter"))
        stops.append({**base, "mode": a, "kind": b,
                      "has_shelter": shelter, "has_shelter_source": "tag" if shelter is not None else None,
                      "wheelchair": t.get("wheelchair") if t.get("wheelchair") in ("yes", "limited", "no") else None,
                      "ele_m": ele_m(t.get("ele")),
                      "summer_access": t.get("aerialway:summer:access") if a == "aerialway" else None})
    else:
        lines.append({**base, "type": "unknown" if a == "yes" else a,
                      "duration_min": duration_min(t.get("aerialway:duration")),
                      "summer_access": t.get("aerialway:summer:access")})
    stats[f"{what}:{a}"] += 1

# ---------------- pending bus shelters -> nearest bus stop within 30 m ----------------
bus = [s for s in stops if s["mode"] == "bus" and s["kind"] == "stop"]
tree = STRtree([Point(s["lon"], s["lat"]) for s in bus])
pending = json.load(open(CLEAN / "_pending_bus_shelters.json", encoding="utf-8"))
unmatched = []
for p in pending:
    cand = tree.query(Point(p["lon"], p["lat"]).buffer(0.0005))     # ~40-55 m box
    # an explicit shelter=no on a stop is respected: such a stop cannot receive the shelter
    best = min(((haversine_m((p["lon"], p["lat"]), (bus[i]["lon"], bus[i]["lat"])), i) for i in cand
                if bus[i]["has_shelter"] is not False), default=None)
    if best and best[0] <= SHELTER_MATCH_M:
        s = bus[best[1]]
        if s["has_shelter"] is not True:
            stats["shelter_set_from_pending"] += 1
            s["has_shelter"], s["has_shelter_source"] = True, "pending_bus_shelter"
        stats["pending_shelter_matched"] += 1
    else:
        unmatched.append(p)

# ---------------- merge same-name stops of the same mode within 100 m ----------------
groups = defaultdict(list)
for s in stops:
    if s["name"]:
        groups[(s["name"].strip().lower(), s["mode"])].append(s)
merged_stops, used = [], set()
for g in groups.values():
    # clusters: single-linkage within MERGE_STOPS_M
    clusters = []
    for s in g:
        hit = [c for c in clusters if any(haversine_m((s["lon"], s["lat"]), (o["lon"], o["lat"])) <= MERGE_STOPS_M for o in c)]
        new = [s] + [o for c in hit for o in c]
        clusters = [c for c in clusters if c not in hit] + [new]
    for c in clusters:
        if len(c) < 2:
            continue
        c.sort(key=lambda s: (s["kind"] != "station", s["osm_id"]))      # a station wins over a platform
        keep = dict(c[0])
        keep["lat"] = round(sum(s["lat"] for s in c) / len(c), 7)
        keep["lon"] = round(sum(s["lon"] for s in c) / len(c), 7)
        m = munis.find(keep["lat"], keep["lon"])
        keep["municipality_istat"], keep["muni_name"] = m["istat"], m["name"]
        keep["kind"] = "station" if any(s["kind"] == "station" for s in c) else "stop"
        vals = [s["has_shelter"] for s in c]
        keep["has_shelter"] = True if True in vals else False if False in vals else None
        keep["has_shelter_source"] = next((s["has_shelter_source"] for s in c if s["has_shelter"] == keep["has_shelter"]), None)
        wc = [s["wheelchair"] for s in c]
        keep["wheelchair"] = next((v for v in ("yes", "limited", "no") if v in wc), None)
        for k in ("operator", "wikidata", "ele_m", "summer_access"):
            keep[k] = keep[k] or next((s[k] for s in c if s[k]), None)
        keep["merged_osm_ids"] = [s["osm_id"] for s in c]
        merged_stops.append(keep)
        used |= {s["osm_id"] for s in c}
        stats["stops_merged_away"] += len(c) - 1
stops = [s for s in stops if s["osm_id"] not in used] + merged_stops

# ---------------- labels ----------------
for s in stops:
    s.setdefault("merged_osm_ids", None)
    s["name_source"] = "name" if s["name"] else "generated"
    s["name"] = s["name"] or f"{LABELS[(s['mode'], s['kind'])]} – {s.pop('muni_name')}"
    s.pop("muni_name", None)
for l in lines:
    l["name_source"] = "name" if l["name"] else "generated"
    l["name"] = l["name"] or f"Impianto – {l['muni_name']}"
    l.pop("muni_name")

ORDER_S = ["osm_id", "name", "name_source", "mode", "kind", "operator", "has_shelter", "has_shelter_source",
           "wheelchair", "summer_access", "ele_m", "lat", "lon", "municipality_istat", "wikidata", "merged_osm_ids"]
ORDER_L = ["osm_id", "name", "name_source", "type", "duration_min", "summer_access", "operator",
           "lat", "lon", "municipality_istat", "wikidata"]
stops = [{k: s[k] for k in ORDER_S} for s in sorted(stops, key=lambda s: s["osm_id"])]
lines = [{k: l[k] for k in ORDER_L} for l in sorted(lines, key=lambda l: l["osm_id"])]

# ---------------- checks / report ----------------
assert len({s["osm_id"] for s in stops}) == len(stops) and len({l["osm_id"] for l in lines}) == len(lines)
print(dict(stats))
print("dropped:", dict(dropped))
print("stops:", len(stops), Counter((s["mode"], s["kind"]) for s in stops))
print("  generated names:", sum(s["name_source"] == "generated" for s in stops),
      "| merged groups:", len(merged_stops),
      "| has_shelter:", Counter(s["has_shelter"] for s in stops),
      "| wheelchair:", Counter(s["wheelchair"] for s in stops if s["wheelchair"]),
      "| aerialway stations summer_access:", Counter(s["summer_access"] for s in stops if s["summer_access"]))
print("  merged groups by mode:", Counter(s["mode"] for s in stops if s["merged_osm_ids"]),
      "| largest:", max((len(s["merged_osm_ids"]), s["name"]) for s in stops if s["merged_osm_ids"]))
print("  operators:", Counter(o for s in stops for o in (s["operator"] or ["<none>"])).most_common(10))
print("pending bus shelters: matched", stats["pending_shelter_matched"], "| unmatched", len(unmatched))
print("lines:", len(lines), Counter(l["type"] for l in lines),
      "| duration:", sum(l["duration_min"] is not None for l in lines),
      "| summer_access:", Counter(l["summer_access"] for l in lines if l["summer_access"]),
      "| generated names:", sum(l["name_source"] == "generated" for l in lines))
seg_lifts = {w["osm_id"] for w in json.load(open(CLEAN / "ways.json", encoding="utf-8")) if w["aerialway"]}
print("lift lines that are also route segments in ways.json:",
      sum(l["osm_id"] in seg_lifts for l in lines), "of", len(seg_lifts))

json.dump(stops, open(CLEAN / "transport_stops.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(lines, open(CLEAN / "aerialways.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(unmatched, open(CLEAN / "_unmatched_bus_shelters.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written: transport_stops.json", len(stops), "| aerialways.json", len(lines),
      "| _unmatched_bus_shelters.json", len(unmatched))
