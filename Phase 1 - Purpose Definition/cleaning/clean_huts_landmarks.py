"""Clean huts_landmarks.json -> huts, landmarks (+ two pending files for later steps).

Input:  data/huts_landmarks.json (Overpass export, 5749 nodes/ways/relations)
Output: data/clean/huts.json                       -> alpine huts, bivouacs, emergency shelters
        data/clean/landmarks.json                  -> peaks, saddles, viewpoints, waterfalls, caves, ...
        data/clean/_pending_bus_shelters.json      -> bus stop shelters, for the public transport step
        data/clean/_pending_rest_areas.json        -> gazebos / picnic shelters / picnic sites, for the mixed_pois step
"""
import json
from collections import Counter

from route_common import BASE
from poi_common import (CLEAN, Municipalities, cuisine_list, ele_m, first_of, norm_operator, osm_key,
                        phones, position, to_int, yes_no)
from shapely.geometry import Point

SRC = BASE / "data" / "huts_landmarks.json"

EMERGENCY_TYPES = {"basic_hut", "lean_to", "rock_shelter", "weather_shelter", "basic", "hut"}
REST_TYPES = {"gazebo", "picnic_shelter", "sun_shelter", "pavilion", "picnic_table", "cabana"}
DROP_SHELTER_TYPES = {"animal_shelter", "field_shelter"}         # shelters for animals
FOOD_AMENITIES = {"restaurant", "bar", "cafe", "fast_food", "pub"}
LANDMARK_NATURAL = {"peak", "saddle", "cave_entrance", "cliff"}
LANDMARK_TOURISM = {"viewpoint", "attraction"}
LABELS = {  # generated labels for unnamed elements
    "alpine_hut": "Rifugio", "wilderness_hut": "Bivacco", "emergency_shelter": "Riparo",
    "peak": "Cima senza nome", "saddle": "Sella", "viewpoint": "Punto panoramico",
    "waterfall": "Cascata", "cave_entrance": "Grotta", "cliff": "Parete rocciosa", "attraction": "Attrazione",
}


def classify(t):
    """-> (target, category). Huts first, then shelters, then natural landmarks, then tourism."""
    tour, am, nat = t.get("tourism"), t.get("amenity"), t.get("natural")
    if tour in ("alpine_hut", "wilderness_hut"):
        return "hut", tour
    if am == "rock_shelter":
        return "hut", "emergency_shelter"
    if am == "shelter":
        st = t.get("shelter_type")
        if st == "public_transport":
            return "bus_shelter", None
        if st in REST_TYPES:
            return "rest_area", st
        if st in DROP_SHELTER_TYPES:
            return "drop", f"shelter_type={st}"
        if st in EMERGENCY_TYPES:
            return "hut", "emergency_shelter"
        # no type (or an unclear one): kept only when named (user decision)
        return ("hut", "emergency_shelter") if t.get("name") else ("drop", "shelter without type and name")
    if nat in LANDMARK_NATURAL:
        return "landmark", nat
    if t.get("waterway") == "waterfall":
        return "landmark", "waterfall"
    if tour in LANDMARK_TOURISM:
        return "landmark", tour
    if tour == "picnic_site":
        return "rest_area", "picnic_site"
    return "drop", f"{'tourism=' + tour if tour else 'amenity=' + str(am)}"


def food_service(t):
    """True only when a tag says so (cuisine, or a food amenity); otherwise None = not verified."""
    am = set((t.get("amenity") or "").split(";"))
    if t.get("cuisine") or am & FOOD_AMENITIES:
        return True, "tag"
    return None, None


munis = Municipalities()
out = {"hut": [], "landmark": [], "bus_shelter": [], "rest_area": []}
stats, dropped = Counter(), Counter()

for el in json.load(open(SRC, encoding="utf-8"))["elements"]:
    t = el["tags"]
    lat, lon = position(el)
    if not munis.province.contains(Point(lon, lat)):
        stats["dropped_outside_province"] += 1
        continue
    target, cat = classify(t)
    if target == "drop":
        dropped[cat] += 1
        continue
    muni = munis.find(lat, lon)
    base = {"osm_id": osm_key(el), "lat": round(lat, 7), "lon": round(lon, 7),
            "municipality_istat": muni["istat"] if muni else None}

    if target in ("bus_shelter", "rest_area"):
        out[target].append({**base, "name": t.get("name"), "type": cat})
        stats[target] += 1
        continue

    if t.get("name"):
        name, name_src = t["name"], "name"
    else:
        name, name_src = f"{LABELS[cat]} – {muni['name'] if muni else 'Trentino'}", "generated"
    common = {"osm_id": base["osm_id"], "name": name, "name_source": name_src, "category": cat,
              "ele_m": ele_m(t.get("ele")), "lat": base["lat"], "lon": base["lon"],
              "municipality_istat": base["municipality_istat"], "wikidata": t.get("wikidata")}

    if target == "hut":
        food, food_src = food_service(t)
        out["hut"].append({
            **common,
            "operator": norm_operator(t.get("operator")),
            "capacity": to_int(t.get("capacity")) if t.get("capacity") else to_int(t.get("beds")),
            "capacity_source": "capacity" if t.get("capacity") else "beds" if to_int(t.get("beds")) is not None else None,
            "winter_room": yes_no(t.get("winter_room")),
            "opening_hours": t.get("opening_hours"),
            "fee": yes_no(t.get("fee")),
            "food_service": food,
            "food_service_source": food_src,
            "cuisine": cuisine_list(t.get("cuisine")),
            "phone": phones(t),
            "email": first_of(t, "email", "contact:email"),
            "website": first_of(t, "website", "contact:website"),
        })
    else:
        out["landmark"].append({**common, "mountain_pass": True if t.get("mountain_pass") == "yes" else None})
    stats[f"{target}:{cat}"] += 1

# ---------------- checks / report ----------------
for k in ("hut", "landmark"):
    assert len({x["osm_id"] for x in out[k]}) == len(out[k])
    assert all(x["municipality_istat"] for x in out[k]), f"{k} without municipality"
print(dict(sorted(stats.items())))
print("dropped:", dict(dropped))
h = out["hut"]
print("huts:", len(h), "| named:", sum(x["name_source"] == "name" for x in h),
      "| food_service true:", sum(bool(x["food_service"]) for x in h),
      "| capacity:", sum(x["capacity"] is not None for x in h),
      "| winter_room:", Counter(x["winter_room"] for x in h),
      "| phone:", sum(bool(x["phone"]) for x in h), "| website:", sum(bool(x["website"]) for x in h))
print("hut operators:", Counter(o for x in h for o in (x["operator"] or ["<none>"])).most_common(12))
lm = out["landmark"]
print("landmarks:", len(lm), "| generated names:", Counter(x["category"] for x in lm if x["name_source"] == "generated"))
print("wikidata: huts", sum(bool(x["wikidata"]) for x in h), "landmarks", sum(bool(x["wikidata"]) for x in lm))
print("ele filled: huts", sum(x["ele_m"] is not None for x in h), "landmarks", sum(x["ele_m"] is not None for x in lm))

for k, f in [("hut", "huts.json"), ("landmark", "landmarks.json"),
             ("bus_shelter", "_pending_bus_shelters.json"), ("rest_area", "_pending_rest_areas.json")]:
    json.dump(sorted(out[k], key=lambda x: x["osm_id"]), open(CLEAN / f, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("written:", CLEAN / f, len(out[k]))
