"""Clean accomodations.json + hotels.json -> accommodations.json (one file for all accommodations).

Input:  data/accomodations.json (Overpass export, 617: guest_house, camp_site, chalet, hostel)
        data/hotels.json        (Overpass export, 1765: hotel, apartment, motel)
Output: data/clean/accommodations.json
"""
import json
from collections import Counter, defaultdict

from shapely.geometry import Point

from route_common import BASE, haversine_m
from poi_common import (CLEAN, Municipalities, cuisine_list, ele_m, first_of, norm_operator, osm_key,
                        phones, position, to_int)

SOURCES = ["accomodations.json", "hotels.json"]
FOOD_AMENITIES = {"restaurant", "bar", "cafe", "fast_food", "pub"}
LABELS = {"guest_house": "Affittacamere", "bed_and_breakfast": "B&B", "agritourism": "Agriturismo",
          "hotel": "Hotel", "apartment": "Appartamenti", "camp_site": "Campeggio", "chalet": "Chalet",
          "hostel": "Ostello", "motel": "Motel"}
# same name + same category + all within this distance -> the same structure, merged (user decision)
MERGE_MAX_DISTANCE_M = 200


def category(t):
    tour = t["tourism"]
    if tour == "guest_house" and t.get("guest_house") in ("bed_and_breakfast", "agritourism", "hotel", "apartment"):
        return t["guest_house"]
    return tour


def yes_no(v, yes=("yes",), no=("no",)):
    return True if v in yes else False if v in no else None


def food_service(t):
    am = set((t.get("amenity") or "").split(";"))
    return (True, "tag") if t.get("cuisine") or am & FOOD_AMENITIES else (None, None)


def build(el, t, src, munis):
    lat, lon = position(el)
    muni = munis.find(lat, lon)
    cat = category(t)
    is_camp = cat == "camp_site"
    food, food_src = food_service(t)
    if t.get("name"):
        name, name_src = t["name"], "name"
    else:
        name, name_src = f"{LABELS[cat]} – {muni['name']}", "generated"
    cap_src = "capacity" if to_int(t.get("capacity")) is not None else "beds" if to_int(t.get("beds")) is not None else None
    return {
        "osm_id": osm_key(el),
        "name": name,
        "name_source": name_src,
        "category": cat,
        "source_dataset": src,
        # stars as integer (user decision): "3S" (superior) -> 3, "3.5" -> 3, "4-5" -> 4 (leading digit)
        "stars": to_int(t.get("stars")),
        "rooms": to_int(t.get("rooms")),
        "capacity": to_int(t.get(cap_src)) if cap_src else None,
        "capacity_source": cap_src,
        "capacity_pitches": to_int(t.get("capacity:pitches")) if is_camp else None,
        "tents": yes_no(t.get("tents")) if is_camp else None,
        "caravans": yes_no(t.get("caravans")) if is_camp else None,
        "motorhome": yes_no(t.get("motorhome")) if is_camp else None,
        "wheelchair": t.get("wheelchair") if t.get("wheelchair") in ("yes", "limited", "no") else None,
        "dog": yes_no(t.get("dog"), yes=("yes", "leashed")),
        "internet_access": yes_no((t.get("internet_access") or "").split(";")[0], yes=("yes", "wlan", "wired")),
        "food_service": food,
        "food_service_source": food_src,
        "cuisine": cuisine_list(t.get("cuisine")),
        "opening_hours": t.get("opening_hours"),
        "operator": norm_operator(t.get("operator")),
        "ele_m": ele_m(t.get("ele")),
        "lat": round(lat, 7),
        "lon": round(lon, 7),
        "municipality_istat": muni["istat"],
        "phone": phones(t),
        "email": (first_of(t, "email", "contact:email") or "").lower() or None,
        "website": first_of(t, "website", "contact:website"),
        "wikidata": t.get("wikidata"),
        "unit_count": 1,
        "merged_osm_ids": None,
    }


munis = Municipalities()
rows, stats, seen = [], Counter(), set()
for src in SOURCES:
    for el in json.load(open(BASE / "data" / src, encoding="utf-8"))["elements"]:
        t, key = el["tags"], osm_key(el)
        if key in seen:
            stats["duplicate_osm_id_across_sources"] += 1
            continue
        seen.add(key)
        lat, lon = position(el)
        if not munis.province.contains(Point(lon, lat)):
            stats[f"dropped_outside_province:{src}"] += 1
            continue
        rows.append(build(el, t, src, munis))
        stats[f"kept:{src}"] += 1

# ---------------- merge the elements of the same structure (both sources together) ----------------
groups = defaultdict(list)
for r in rows:
    if r["name_source"] == "name":
        groups[(r["name"].strip().lower(), r["category"])].append(r)


def max_pair_distance(g):
    return max(haversine_m((a["lon"], a["lat"]), (b["lon"], b["lat"])) for a in g for b in g)


merged_out = []
for (n, cat), g in groups.items():
    if len(g) < 2 or max_pair_distance(g) > MERGE_MAX_DISTANCE_M:
        continue
    g_max = round(max_pair_distance(g))
    g.sort(key=lambda r: r["osm_id"])
    keep = g[0]
    keep["lat"] = round(sum(r["lat"] for r in g) / len(g), 7)
    keep["lon"] = round(sum(r["lon"] for r in g) / len(g), 7)
    keep["municipality_istat"] = munis.find(keep["lat"], keep["lon"])["istat"]
    keep["unit_count"] = len(g)
    keep["merged_osm_ids"] = [r["osm_id"] for r in g]
    for r in g[1:]:
        for k, v in r.items():                      # fill fields missing in the kept one
            if keep.get(k) is None and v is not None:
                keep[k] = v
        rows.remove(r)
    merged_out.append((keep["name"], cat, len(g), g_max))
    stats["merged_elements"] += len(g) - 1

# same-name groups farther apart: different places, not merged
other = [(g[0]["name"], cat, len(g), round(max_pair_distance(g)))
         for (n, cat), g in groups.items() if len(g) > 1 and max_pair_distance(g) > MERGE_MAX_DISTANCE_M]

# ---------------- checks / report ----------------
assert len({r["osm_id"] for r in rows}) == len(rows)
print(dict(stats))
print(f"merged groups: {len(merged_out)} | by category:", Counter(m[1] for m in merged_out))
print("  largest:", sorted(merged_out, key=lambda m: -m[2])[:5])
print("  farthest:", sorted(merged_out, key=lambda m: -m[3])[:5])
print(f"same-name groups NOT merged (farther than {MERGE_MAX_DISTANCE_M} m): {len(other)}",
      sorted(other, key=lambda o: o[3])[:8])
print("category:", Counter(r["category"] for r in rows))
print("source_dataset:", Counter(r["source_dataset"] for r in rows))
print("stars:", sorted(Counter(r["stars"] for r in rows if r["stars"] is not None).items()))
print("generated names:", sum(r["name_source"] == "generated" for r in rows))
for k in ["stars", "rooms", "capacity", "capacity_pitches", "tents", "caravans", "motorhome", "wheelchair",
          "dog", "internet_access", "food_service", "cuisine", "opening_hours", "operator", "ele_m",
          "phone", "email", "website", "wikidata"]:
    print(f"{k}: {sum(r[k] is not None for r in rows)}")

json.dump(sorted(rows, key=lambda r: r["osm_id"]), open(CLEAN / "accommodations.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("written:", CLEAN / "accommodations.json", len(rows))
