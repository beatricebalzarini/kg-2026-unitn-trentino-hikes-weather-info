# Cleaning: amenities.json → food_drink.json

- **Source**: `data/amenities.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_amenities.py` (shared POI helpers in `cleaning/poi_common.py`)
- **Other inputs**: raw `data/huts_landmarks.json`, `data/accomodations.json` and `data/hotels.json` (to find the overlaps), `data/clean/huts.json` and `data/clean/accommodations.json` (they must be produced first), `data/clean/municipalities_boundaries.geojson`
- **Output**: `data/clean/food_drink.json`: **3004** places to eat and drink

The output is named `food_drink` instead of `amenities`: `amenity` is a generic OSM key, and the name would clash with other uses in the KG.

## Input
3145 elements: 2426 `node`, 717 `way`, 2 `relation` (position from `center`). All inside the province.
`amenity`: restaurant 1512, bar 720, cafe 618, fast_food 208, pub 87. 2922 have a name. 145 also have a `tourism` tag (hotel 69, alpine_hut 47, guest_house 18, ...).

## Overlaps with other datasets (same `osm_id`)
The same building must not be two entities. In both cases the tags are **identical** in the two source files, so nothing is lost.

| With | Count | Decision |
|---|---|---|
| `huts_landmarks.json` → `huts.json` | 48 (alpine huts with a restaurant) | **excluded here**, kept only in `huts.json` with `food_service = true` and `cuisine` (checked: all 48 are in `huts.json`) |
| `accomodations.json` + `hotels.json` → `accommodations.json` | 93 (20 guest houses / agritourisms + 73 hotels with a restaurant or bar) | **excluded here** (user decision, same as the huts), kept only in `accommodations.json` with `food_service = true` and `cuisine` (checked: all 93 are there, also inside `merged_osm_ids`) |

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| Already in `huts.json` | 48 | see above |
| Already in `accommodations.json` | 93 | see above |
| Outside the province polygon | 0 | all inside |

No filter on the distance from the trails: the link "food near a trail" (CQ #4) will be computed in the spatial-join phase (distance to be decided, e.g. 500 m).

## Output fields
| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"{type}/{id}"` | key |
| `name` | `name`; if missing, generated `"{type} – {municipality}"` (e.g. "Bar – Trento"), 223 | label |
| `name_source` | `name` or `generated` | provenance |
| `category` | `amenity`: restaurant 1382, bar 714, cafe 614, fast_food 208, pub 86 | #4 |
| `cuisine` | list: lowercase, split on `;`/`,`, `italian_pizza` → `pizza` (978 filled; top: pizza 440, regional 296, italian 292) | #4 |
| `opening_hours` | as is (768) | – |
| `wheelchair` | `yes` / `limited` / `no`; `designated` → `yes` (363) | elderly/disabled persona |
| `outdoor_seating` | `yes`, `terrace`, `veranda`, `garden`, `pedestrian_zone` → true; `no` → false (786) | user info (kept, user decision) |
| `takeaway` | `yes` / `no` / `only` (184) | user info (kept, user decision) |
| `diet_vegetarian`, `diet_vegan`, `diet_gluten_free` | `yes` / `no` / `limited` / `only` (138, 98, 30) | user info (kept, user decision) |
| `lat`, `lon` | node position or `center` | spatial joins |
| `municipality_istat` | point-in-polygon with the municipalities | #22 |
| `phone` | list from `phone` + `contact:phone` + `contact:mobile`, normalized as for the huts (871) | contacts |
| `email` | `email`, else `contact:email`, lowercased (260) | contacts |
| `website` | `website`, else `contact:website` (479) | contacts |
| `wikidata` | as is (7; the others belong to the excluded huts/accommodations) | linking |

## Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `addr:*` | the municipality comes from the coordinates |
| `ref:vatin`, `ref:pat:id`, `ref:pat:cat`, `ref:rea_tn`, `ref:it:vat` | official/administrative references (user todo) |
| `check_date*`, `opening_hours:signed`, `source`, `building*` | editing metadata and building details |
| `payment:*`, `contact:facebook`, `contact:instagram` and other social links | not used by any CQ |
| `smoking`, `toilets`, `internet_access`, `delivery`, `reservation`, `indoor_seating` | not used by any CQ |
| `tourism` | only used to find the overlaps |
| `name:*`, `alt_name`, `description`, `note`, `wikipedia` | name variants and free text (`wikidata` kept) |

## Checks (all passed)
- `osm_id` unique.
- Every place falls inside a municipality.
- The 48 excluded huts are all in `huts.json`; the 93 excluded accommodations are all in `accommodations.json`.

## Final count
After the cross-file step (`dedup_cross_files.py`, see `cross_file_duplicates.md`): **2957** (47 duplicates of huts and accommodations mapped with a different OSM id removed).
