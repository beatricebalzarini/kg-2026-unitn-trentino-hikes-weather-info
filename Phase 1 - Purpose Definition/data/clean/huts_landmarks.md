# Cleaning: huts_landmarks.json → huts.json + landmarks.json

- **Source**: `data/huts_landmarks.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_huts_landmarks.py` (shared POI helpers in `cleaning/poi_common.py`)
- **Other input**: `data/clean/municipalities_boundaries.geojson` (municipality of each point)
- **Outputs**:
  - `data/clean/huts.json`: **745** places to sleep or take shelter (alpine huts, bivouacs, emergency shelters)
  - `data/clean/landmarks.json`: **4386** natural landmarks (peaks, saddles, viewpoints, caves, waterfalls, cliffs)
  - `data/clean/_pending_bus_shelters.json`: 203 bus stop shelters, **for the public transport step**
  - `data/clean/_pending_rest_areas.json`: 268 gazebos / picnic shelters, **for the mixed_pois step** (category `rest_area`)

## Input
5749 elements: 4674 `node` (`lat`/`lon`), 1073 `way` and 2 `relation` (position in `center`). Every element has a position. 5724 are inside the province.

Main categories: `natural=peak` 1976, `tourism=viewpoint` 939, `amenity=shelter` 938, `natural=saddle` 717, `natural=cave_entrance` 522, `tourism=alpine_hut` 235, `waterway=waterfall` 231, `tourism=wilderness_hut` 161, plus a few cliffs, attractions, information points, picnic sites and one place of worship. Tags often co-occur (e.g. a saddle also tagged `tourism=information`).

## Classification
Each element gets **exactly one category**, by the first rule that matches:

| # | Rule | Category | Goes to |
|---|---|---|---|
| 1 | `tourism=alpine_hut` | `alpine_hut` (staffed hut, "rifugio") | `huts.json` |
| 2 | `tourism=wilderness_hut` | `wilderness_hut` (bivouac, "bivacco") | `huts.json` |
| 3 | `amenity=rock_shelter` | `emergency_shelter` | `huts.json` |
| 4 | `amenity=shelter` + `shelter_type=public_transport` | bus shelter | `_pending_bus_shelters.json` |
| 5 | `amenity=shelter` + `shelter_type` = gazebo, picnic_shelter, sun_shelter, pavilion, picnic_table, cabana | rest area | `_pending_rest_areas.json` |
| 6 | `amenity=shelter` + `shelter_type` = animal_shelter, field_shelter | – | dropped (shelters for animals) |
| 7 | `amenity=shelter` + `shelter_type` = basic_hut, lean_to, rock_shelter, weather_shelter, basic, hut | `emergency_shelter` | `huts.json` |
| 8 | `amenity=shelter` with no (or an unclear) `shelter_type`: **kept only if it has a name** (user decision) | `emergency_shelter` | `huts.json` |
| 9 | `natural` = peak, saddle, cave_entrance, cliff | same | `landmarks.json` |
| 10 | `waterway=waterfall` | `waterfall` | `landmarks.json` |
| 11 | `tourism` = viewpoint, attraction | same | `landmarks.json` |
| 12 | `tourism=picnic_site` | rest area | `_pending_rest_areas.json` |

Notes:
- **Bus shelters are not dropped**: they are the roofs of bus stops. In the public transport step each one will be matched to the nearest stop (about 30 m) to set `has_shelter` on the stop, avoiding duplicates.
- **Gazebos and picnic shelters are not dropped**: they will be merged with `mixed_pois` as rest areas.
- **The only `amenity=place_of_worship`** is "Madonnina della Luce", a cave (`natural=cave_entrance`) with a statue of the Virgin Mary: by the rules above it is a `cave_entrance` landmark.
- The elements tagged `tourism=information`, `attraction` or `picnic_site` all co-occur with a stronger tag (saddle, cave, waterfall, shelter) and are classified by it.

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| Outside the province polygon | 25 | outside Trentino |
| Shelter without `shelter_type` and without `name` | 120 | cannot tell a real shelter from a gazebo, and no label (user decision) |
| Shelters for animals (`animal_shelter`, `field_shelter`) | 2 | not for people |

## Output fields

### `huts.json`
| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"{type}/{id}"` (e.g. `node/123`): OSM ids are unique only together with the type | key |
| `name` | `name`; if missing, generated label (see below) | label |
| `name_source` | `name` or `generated` | provenance |
| `category` | `alpine_hut` 234, `wilderness_hut` 160, `emergency_shelter` 351 | #5, alpinist persona (bivouacs) |
| `ele_m` | `ele` → integer metres (344 filled) | #9 |
| `lat`, `lon` | node position or `center` | spatial joins |
| `municipality_istat` | point-in-polygon with the municipalities | #22 |
| `wikidata` | as is (94); kept wherever present (user decision) | linking |
| `operator` | list, normalized: every SAT spelling and section ("Società degli Alpinisti Tridentini", "SAT Ala", "S.A.T. Aldeno", "sezione SAT di Storo", ...) → `SAT`; CAI sections → `CAI`; AVS → `AVS`; "privato" → `private`; a pair of coordinates written as operator is dropped. Operators that are names of private persons (managers/owners) are kept as they are: they are public OSM data (user decision) | – |
| `capacity` | `capacity` → integer; if missing, `beds` (110 filled) | #5 |
| `capacity_source` | `capacity` 94, `beds` 17, `null` | provenance |
| `winter_room` | `yes`/`no` → boolean (34 filled) | #5, winter |
| `opening_hours` | as is (free OSM syntax, also Italian text) | – |
| `fee` | `yes`/`no` → boolean (`donation` → null) | – |
| `food_service` | **`true` only if a tag says so**: `cuisine` set, or `amenity` = restaurant / bar / cafe / fast_food / pub (also multi-valued, e.g. `restaurant;cafe`). **Otherwise `null` = not verified**: it is not inferred from `alpine_hut` (user decision) | #4 |
| `food_service_source` | `tag` or `null` | provenance |
| `cuisine` | `cuisine` → list (lowercase, split on `;`/`,`, `italian_pizza` → `pizza`), 23 huts. Added in the amenities step: 48 huts are also in `amenities.json` with identical tags, so they are kept only here (see `food_drink.md`) | #4 |
| `phone` | list from `phone` + `contact:phone` + `contact:mobile` + `mobile`: multiple numbers split on `;`, spaces/dashes removed, `00` → `+`, `+39` added when missing, deduplicated | contacts (kept for now, user decision) |
| `email` | `email`, else `contact:email` | contacts |
| `website` | `website`, else `contact:website` | contacts |

### `landmarks.json`
| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id`, `name`, `name_source`, `category`, `ele_m`, `lat`, `lon`, `municipality_istat`, `wikidata` | as for the huts | #21, student persona (≥ 3 landmarks), #9 |
| `category` | `peak` 1973, `viewpoint` 932, `saddle` 712, `cave_entrance` 526, `waterfall` 233, `cliff` 10 | |
| `mountain_pass` | `true` when `mountain_pass=yes` (354 saddles), else `null` | – |

### Generated labels
Unnamed elements are **not dropped** (user decision). They get `"{type} – {municipality}"`, with `name_source = "generated"`:

| Category | Label | Generated |
|---|---|---|
| viewpoint | "Punto panoramico – Pergine Valsugana" | 776 |
| cave_entrance | "Grotta – …" | 254 |
| peak | "Cima senza nome – …" | 206 |
| waterfall | "Cascata – …" | 130 |
| saddle | "Sella – …" | 89 |
| cliff | "Parete rocciosa – …" | 6 |
| emergency_shelter | "Riparo – …" (typed shelters only) | 116 |
| wilderness_hut | "Bivacco – …" | 11 |
| alpine_hut | "Rifugio – …" | 2 |

Generated labels are not unique (several "Punto panoramico – Tenno"): the key is always `osm_id`.

### Pending files
- `_pending_bus_shelters.json`: `osm_id`, `name`, `type` (`null`), `lat`, `lon`, `municipality_istat`.
- `_pending_rest_areas.json`: same fields, `type` = gazebo 213, picnic_shelter 49, sun_shelter 2, pavilion 2, picnic_table 1, cabana 1 (+ picnic sites, here 0 because they all co-occur with a shelter tag).

## Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `building`, `building:levels`, `layer`, `material`, `width`, `height`, `lit` | building details |
| `wikipedia`, `wikimedia_commons`, `image`, `source*`, `note`, `fixme`, `check_date`, `importance`, `prominence`, `name:etymology:wikidata`, `it:lombardia:*` | links and editing metadata (`wikidata` is kept) |
| `name:*`, `alt_name`, `loc_name`, `old_name`, `description*` | name variants and free text |
| `summit:cross`, `summit:register`, `direction`, `start_date`, `disused:*`, `old:military`, `historic`, `man_made`, `intermittent` | not used by any CQ |
| `bench`, `bin`, `fireplace`, `mattress`, `drinking_water`, `toilets`, `shower`, `power_supply`, `internet_access`, `outdoor_seating`, `backrest`, `locked`, `lockable` | hut furniture/services not used by any CQ |
| `access`, `reservation`, `owner`, `ownership`, `wheelchair` | not used by any CQ |
| `addr:*`, `contact:facebook` etc., `ref:vatin`, `ref`, `source:ref` | address and administrative ids (the municipality comes from the point) |
| `shelter_type` | used only for the classification |

## Results
- `huts.json`: 745 (234 alpine huts, 160 bivouacs, 351 emergency shelters: 164 untyped but named, 63 lean_to, 49 basic_hut, 37 rock_shelter, 25 weather_shelter, 8 basic, 2 hut, 2 `amenity=rock_shelter`, 1 `building`).
  - `food_service = true`: 58 (57 alpine huts, 1 bivouac); all others `null` (not verified).
  - Operator: SAT 57, private 10, CAI 9, others; 631 without operator.
  - Contacts: phone 105, website 120.
- `landmarks.json`: 4386 (2925 with a real name).

## Checks (all passed)
- `osm_id` unique in each output.
- Every hut and landmark falls inside a municipality.

## Overlap with amenities.json
48 objects of this file are also in `amenities.json` (same `osm_id`, **identical tags**): alpine huts with a restaurant. They are kept **only in `huts.json`** (with `food_service = true` and `cuisine`) and excluded from `food_drink.json`, so the same building is not two entities.

## Open points
- Missing `ele_m` (401 huts, 1831 landmarks) can be filled by the DEM enrichment, if done.

## Final count
After the cross-file step (`dedup_cross_files.py`, see `cross_file_duplicates.md`): huts absorb 7 duplicates (6 from `food_drink.json`, 1 from `accommodations.json`) and landmarks 2 (from `cultural_landmarks.json`), listed in `duplicates`. Counts unchanged.
