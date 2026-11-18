"""Clean mixed_pois.json -> water points, cultural landmarks, guideposts, tourist info, rest areas.

Input:  data/mixed_pois.json (Overpass export, 17958 nodes/ways/relations)
        data/clean/{huts,landmarks,food_drink,accommodations,_pending_rest_areas,_pending_bus_shelters}.json
            (objects already cleaned elsewhere are excluded)
        data/clean/{trails,mtb,foot_routes}.json (guidepost_node_ids of the kept routes)
        data/clean/_pending_rest_areas.json (rest areas parked by clean_huts_landmarks.py)
Output: data/clean/water_points.json, cultural_landmarks.json, guideposts.json, tourist_info.json,
        rest_areas.json, _pending_accommodations.json
"""
import json
from collections import Counter

from shapely.geometry import Point

from route_common import BASE
from poi_common import CLEAN, Municipalities, ele_m, osm_key, position

SRC = BASE / "data" / "mixed_pois.json"

ACCOMMODATION_TOURISM = {"hotel", "guest_house", "hostel", "motel", "apartment", "chalet", "camp_site"}
MILITARY_HISTORIC = {"bunker", "trench", "battlefield", "cannon", "ww1", "military"}
# historic values that are the same thing as a main category
HISTORIC_ALIASES = {"church": "place_of_worship", "wayside_chapel": "place_of_worship", "chapel": "place_of_worship",
                    "monastery": "place_of_worship", "fortification": "fort", "mine_shaft": "mine",
                    "cemetery": "grave_yard", "tombstone": "tomb"}
RARE_CATEGORY_MAX = 4          # cultural categories with <= this many elements are collapsed into historic_other
TOURIST_INFO = {"office", "visitor_centre", "Pro_Loco_Cles"}
CULTURAL_TOURISM = {"attraction", "artwork", "museum", "viewpoint"}
CULTURAL_AMENITY = {"place_of_worship", "grave_yard"}
LABELS = {
    "drinking_water": "Fontanella", "fountain": "Fontana", "guidepost": "Cartello", "office": "Ufficio turistico",
    "rest_area": "Area di sosta",
    "wayside_shrine": "Capitello", "wayside_cross": "Croce", "memorial": "Memoriale", "monument": "Monumento",
    "ruins": "Rudere", "castle": "Castello", "fort": "Forte", "archaeological_site": "Sito archeologico",
    "mine": "Miniera", "military_remains": "Resto militare", "boundary_stone": "Cippo di confine",
    "place_of_worship": "Luogo di culto", "grave_yard": "Cimitero", "attraction": "Attrazione",
    "artwork": "Opera d'arte", "museum": "Museo", "viewpoint": "Punto panoramico", "lime_kiln": "Calchera",
    "milestone": "Pietra miliare", "tomb": "Tomba", "historic_other": "Punto storico",
}


def classify(t, key, route_posts):
    """-> (output, category) or ('drop', reason). One category per element, first rule that matches."""
    tour, am, hist, info = t.get("tourism"), t.get("amenity"), t.get("historic"), t.get("information")
    if tour in ACCOMMODATION_TOURISM:
        return "accommodation", tour
    if am == "shelter":
        return "rest_area", t.get("shelter_type")
    if am in ("drinking_water", "fountain"):
        return "water", am
    if hist:
        if hist in MILITARY_HISTORIC or (hist in ("yes", "no") and (t.get("military") or t.get("bunker_type"))):
            return "cultural", "military_remains"
        if hist == "yes":
            return ("cultural", "historic_other") if t.get("name") else ("drop", "historic=yes without name/military")
        if hist != "no":                              # historic=no means "not historic": use the other tags
            return "cultural", HISTORIC_ALIASES.get(hist, hist)
    if am in CULTURAL_AMENITY:
        return "cultural", am
    if tour in CULTURAL_TOURISM:
        return "cultural", tour
    if tour == "information":
        if info == "guidepost":
            if key in route_posts or t.get("name"):
                return "guidepost", "guidepost"
            return "drop", "guidepost without name, not on a kept route"
        if info in TOURIST_INFO:
            return "tourist_info", "visitor_centre" if info == "visitor_centre" else "office"
        return "drop", f"information={info}"
    return "drop", f"other ({tour or am or hist})"


def drinking(t, cat):
    if t.get("drinking_water") == "no":
        return False
    if cat == "drinking_water" or t.get("drinking_water") == "yes" or t.get("fountain") in ("drinking", "bubbler"):
        return True
    return None


# objects already cleaned in another file (same osm_id): excluded here
already = {}
for f in ["huts", "landmarks", "food_drink", "accommodations", "_pending_rest_areas", "_pending_bus_shelters"]:
    for r in json.load(open(CLEAN / f"{f}.json", encoding="utf-8")):
        for i in r.get("merged_osm_ids") or [r["osm_id"]]:
            already[i] = f
route_posts = {i for f in ("trails", "mtb", "foot_routes")
               for r in json.load(open(CLEAN / f"{f}.json", encoding="utf-8")) for i in r["guidepost_node_ids"]}

munis = Municipalities()
out = {k: [] for k in ("water", "cultural", "guidepost", "tourist_info", "rest_area", "accommodation")}
stats, dropped, excluded = Counter(), Counter(), Counter()

for el in json.load(open(SRC, encoding="utf-8"))["elements"]:
    t, key = el["tags"], osm_key(el)
    if key in already:
        excluded[already[key]] += 1
        continue
    lat, lon = position(el)
    if not munis.province.contains(Point(lon, lat)):
        stats["dropped_outside_province"] += 1
        continue
    target, cat = classify(t, key, route_posts)
    if target == "drop":
        dropped[cat] += 1
        continue
    muni = munis.find(lat, lon)
    label_key = "rest_area" if target == "rest_area" else cat
    if t.get("name"):
        name, name_src = t["name"], "name"
    else:
        name, name_src = f"{LABELS.get(label_key, LABELS['historic_other'])} – {muni['name']}", "generated"
    row = {"osm_id": key, "name": name, "name_source": name_src, "category": cat,
           "ele_m": ele_m(t.get("ele")), "lat": round(lat, 7), "lon": round(lon, 7),
           "municipality_istat": muni["istat"], "wikidata": t.get("wikidata")}
    if target == "water":
        row["drinking"] = drinking(t, cat)
    if target == "guidepost":
        row["on_kept_route"] = key in route_posts
    if target in ("rest_area", "accommodation"):
        row = {"osm_id": key, "name": t.get("name"), "type": cat, "lat": row["lat"], "lon": row["lon"],
               "municipality_istat": muni["istat"]}
    out[target].append(row)
    stats[f"{target}:{cat}"] += 1

# rare cultural categories -> historic_other (the original value stays in `subtype`)
counts = Counter(r["category"] for r in out["cultural"])
for r in out["cultural"]:
    r["subtype"] = None
    if counts[r["category"]] <= RARE_CATEGORY_MAX and r["category"] not in ("historic_other", "grave_yard"):
        r["subtype"], r["category"] = r["category"], "historic_other"
        if r["name_source"] == "generated":
            muni_n = r["name"].split(" – ", 1)[1]
            r["name"] = f"{LABELS['historic_other']} – {muni_n}"

# rest areas: add the ones parked by clean_huts_landmarks.py, with the same naming rule
muni_name = {m["istat"]: m["name"] for m in json.load(open(CLEAN / "municipalities.json", encoding="utf-8"))}
pending = json.load(open(CLEAN / "_pending_rest_areas.json", encoding="utf-8"))
rest = []
for r in pending + out["rest_area"]:
    src = "name" if r["name"] else "generated"
    rest.append({"osm_id": r["osm_id"],
                 "name": r["name"] or f"{LABELS['rest_area']} – {muni_name[r['municipality_istat']]}",
                 "name_source": src, "type": r["type"], "lat": r["lat"], "lon": r["lon"],
                 "municipality_istat": r["municipality_istat"]})

# ---------------- checks / report ----------------
files = {"water": "water_points.json", "cultural": "cultural_landmarks.json", "guidepost": "guideposts.json",
         "tourist_info": "tourist_info.json", "accommodation": "_pending_accommodations.json"}
print("excluded (already in):", dict(excluded))
print("dropped:", dict(dropped), "| outside province:", stats.pop("dropped_outside_province", 0))
for k in files:
    rows = out[k]
    assert len({r["osm_id"] for r in rows}) == len(rows)
    print(f"{files[k]}: {len(rows)}", dict(Counter(r.get("category", r.get("type")) for r in rows).most_common(30)))
    if rows and "name_source" in rows[0]:
        print("   generated names:", sum(r["name_source"] == "generated" for r in rows),
              "| wikidata:", sum(bool(r.get("wikidata")) for r in rows),
              "| ele:", sum(r.get("ele_m") is not None for r in rows))
assert len({r["osm_id"] for r in rest}) == len(rest)
print(f"rest_areas.json: {len(rest)} (pending {len(pending)} + here {len(out['rest_area'])})",
      dict(Counter(r["type"] for r in rest)))
print("water drinking:", Counter(r["drinking"] for r in out["water"]))
print("guideposts on kept route:", sum(r["on_kept_route"] for r in out["guidepost"]),
      "of", len(route_posts), "referenced")

for k, f in files.items():
    json.dump(sorted(out[k], key=lambda r: r["osm_id"]), open(CLEAN / f, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
json.dump(sorted(rest, key=lambda r: r["osm_id"]), open(CLEAN / "rest_areas.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("written:", ", ".join(list(files.values()) + ["rest_areas.json"]))
