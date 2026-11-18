"""Clean amenities.json -> food_drink.json (restaurants, bars, cafes, fast food, pubs).

Input:  data/amenities.json        (Overpass export, 3145 nodes/ways/relations)
        data/huts_landmarks.json   (raw: to exclude the objects already cleaned as huts)
        data/accomodations.json, data/hotels.json (raw: to exclude the objects already cleaned as accommodations)
        data/clean/huts.json, data/clean/accommodations.json (must be produced first)
Output: data/clean/food_drink.json
"""
import json
from collections import Counter

from shapely.geometry import Point

from route_common import BASE
from poi_common import CLEAN, Municipalities, cuisine_list, first_of, osm_key, phones, position

SRC = BASE / "data" / "amenities.json"
LABELS = {"restaurant": "Ristorante", "bar": "Bar", "cafe": "Caffè", "fast_food": "Fast food", "pub": "Pub"}
OUTDOOR_YES = {"yes", "terrace", "veranda", "garden", "pedestrian_zone"}
ENUM = {"yes", "no", "limited", "only"}


def wheelchair(v):
    return "yes" if v == "designated" else v if v in ("yes", "limited", "no") else None


def outdoor(v):
    return True if v in OUTDOOR_YES else False if v == "no" else None


def enum(v):
    return v if v in ENUM else None


huts = {osm_key(x) for x in json.load(open(BASE / "data" / "huts_landmarks.json", encoding="utf-8"))["elements"]}
huts_clean = {x["osm_id"] for x in json.load(open(CLEAN / "huts.json", encoding="utf-8"))}
accom = {osm_key(x) for f in ("accomodations.json", "hotels.json")
         for x in json.load(open(BASE / "data" / f, encoding="utf-8"))["elements"]}
accom_clean = set()
for a in json.load(open(CLEAN / "accommodations.json", encoding="utf-8")):
    accom_clean |= set(a["merged_osm_ids"] or [a["osm_id"]])
munis = Municipalities()
rows, stats = [], Counter()

for el in json.load(open(SRC, encoding="utf-8"))["elements"]:
    t, key = el["tags"], osm_key(el)
    if key in huts:
        # same OSM object (identical tags) already in huts.json, with food_service and cuisine
        stats["excluded_already_hut"] += 1
        assert key in huts_clean, f"{key} is in huts_landmarks.json but was not kept in huts.json"
        continue
    if key in accom:
        # same OSM object (identical tags) already in accommodations.json, with food_service and cuisine
        stats["excluded_already_accommodation"] += 1
        assert key in accom_clean, f"{key} is in accomodations.json but was not kept in accommodations.json"
        continue
    lat, lon = position(el)
    if not munis.province.contains(Point(lon, lat)):
        stats["dropped_outside_province"] += 1
        continue
    muni = munis.find(lat, lon)
    cat = t["amenity"]
    if t.get("name"):
        name, name_src = t["name"], "name"
    else:
        name, name_src = f"{LABELS[cat]} – {muni['name']}", "generated"
    rows.append({
        "osm_id": key,
        "name": name,
        "name_source": name_src,
        "category": cat,
        "cuisine": cuisine_list(t.get("cuisine")),
        "opening_hours": t.get("opening_hours"),
        "wheelchair": wheelchair(t.get("wheelchair")),
        "outdoor_seating": outdoor(t.get("outdoor_seating")),
        "takeaway": enum(t.get("takeaway")),
        "diet_vegetarian": enum(t.get("diet:vegetarian")),
        "diet_vegan": enum(t.get("diet:vegan")),
        "diet_gluten_free": enum(t.get("diet:gluten_free")),
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "municipality_istat": muni["istat"],
        "phone": phones(t),
        "email": (first_of(t, "email", "contact:email") or "").lower() or None,
        "website": first_of(t, "website", "contact:website"),
        "wikidata": t.get("wikidata"),
    })
    stats["kept"] += 1

# ---------------- checks / report ----------------
assert len({r["osm_id"] for r in rows}) == len(rows)
print(dict(stats))
print("category:", Counter(r["category"] for r in rows))
print("generated names:", sum(r["name_source"] == "generated" for r in rows))
for k in ["cuisine", "opening_hours", "wheelchair", "outdoor_seating", "takeaway", "diet_vegetarian",
          "diet_vegan", "diet_gluten_free", "phone", "email", "website", "wikidata"]:
    print(f"{k}: {sum(r[k] is not None for r in rows)}")
print("top cuisines:", Counter(c for r in rows for c in (r["cuisine"] or [])).most_common(10))

json.dump(sorted(rows, key=lambda r: r["osm_id"]), open(CLEAN / "food_drink.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("written:", CLEAN / "food_drink.json", len(rows))
