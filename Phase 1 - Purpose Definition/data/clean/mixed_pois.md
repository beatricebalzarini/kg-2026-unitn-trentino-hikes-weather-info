# Cleaning: mixed_pois.json → water points, cultural landmarks, guideposts, tourist info, rest areas

- **Source**: `data/mixed_pois.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_mixed_pois.py` (shared POI helpers in `cleaning/poi_common.py`)
- **Other inputs**: the cleaned `huts`, `landmarks`, `food_drink`, `accommodations` and the two `_pending_*` files (to exclude objects already cleaned), `trails`/`mtb`/`foot_routes` (`guidepost_node_ids`), `_pending_rest_areas.json`, `municipalities_boundaries.geojson`
- **Outputs**:

| File | Count | Content |
|---|---|---|
| `data/clean/water_points.json` | 3950 | drinking water points and fountains |
| `data/clean/cultural_landmarks.json` | 4914 | wayside shrines and crosses, ruins, memorials, WWI remains, castles, forts, archaeological sites, mines, churches, attractions, ... |
| `data/clean/guideposts.json` | 1352 | trail signposts on a kept route or with a name |
| `data/clean/tourist_info.json` | 105 | tourist information offices and visitor centres |
| `data/clean/rest_areas.json` | 268 | gazebos, picnic shelters, ... (the ones parked by `clean_huts_landmarks.py`; none from this file) |
| `data/clean/_pending_accommodations.json` | 0 | was 4 hotels before `hotels.json` was cleaned; now they are in `accommodations.json` and excluded here, so the file is empty |

## Input
17,958 elements: 16,525 `node`, 1389 `way`, 44 `relation` (position from `center`). 17,940 inside the province. Tags often co-occur (`tourism`, `historic`, `amenity`). Only 3895 have a name.

## Excluded / dropped
| Rule | Count | Why |
|---|---|---|
| Same `osm_id` already cleaned in another file | 167 (landmarks 141, accommodations 9, huts 8, food_drink 7, rest areas 2) | the same object must not be two entities |
| Outside the province polygon | 18 | outside Trentino |
| Guidepost without `name` and not referenced by a kept route | 5037 | no information (user decision 1b) |
| Information boards, maps, route markers, signs, terminals and other `information=*` (board 1471, map 388, route_marker 216, none 95, sign/yes/loc_name ~30, ...) | ~2235 | panels: not used by any CQ (user decision) |
| `historic=yes` without name and without military tags | 194 | unknown object (user decision) |

## Classification
Each element gets **exactly one category**, by the first rule that matches:

| # | Rule | Output / category |
|---|---|---|
| 1 | `tourism` = hotel, guest_house, hostel, motel, apartment, chalet, camp_site | `_pending_accommodations.json` |
| 2 | `amenity=shelter` | `rest_areas.json` (none left here after the exclusions) |
| 3 | `amenity` = drinking_water, fountain | `water_points.json` |
| 4 | `historic` = bunker, trench, battlefield, cannon, ww1, military; or `historic` = yes/no with a `military` or `bunker_type` tag | `cultural_landmarks.json`, `military_remains` |
| 5 | `historic=yes` with a name | `cultural_landmarks.json`, `historic_other` |
| 6 | any other `historic` value except `no` (aliases: church / wayside_chapel / chapel / monastery → `place_of_worship`, fortification → `fort`, mine_shaft → `mine`, cemetery → `grave_yard`, tombstone → `tomb`) | `cultural_landmarks.json`, that value |
| 7 | `amenity` = place_of_worship, grave_yard | `cultural_landmarks.json` |
| 8 | `tourism` = attraction, artwork, museum, viewpoint | `cultural_landmarks.json` |
| 9 | `information=guidepost`, kept only if on a kept route or named | `guideposts.json` |
| 10 | `information` = office, visitor_centre (and one "Pro_Loco_Cles") | `tourist_info.json` |
| 11 | everything else | dropped |

`historic=no` means "not historic": those elements skip rule 6 and are classified by their other tags (3 of them are WWI bunkers by `military=bunker`).

**Rare cultural categories**: categories with 4 or fewer elements (watermill, bridge, locomotive, aircraft, icehouse, ...) are collapsed into `historic_other`, and the original value is kept in `subtype`. Exception: `grave_yard` is kept as its own category (cemeteries were explicitly kept, user decision).

**Cemeteries**: all 7 are kept as cultural landmarks. Most are WWI military cemeteries tagged `historic=ww1`, so they fall into `military_remains` (4); 2 are `memorial`, 1 is `grave_yard`.

## Output fields
Common to water points, cultural landmarks, guideposts and tourist info:

| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"{type}/{id}"` | key |
| `name` | `name`; if missing, generated `"{type} – {municipality}"` (e.g. "Fontanella – Ledro", "Capitello – Arco", "Cartello – Predazzo") | label |
| `name_source` | `name` or `generated` | provenance |
| `category` | see Classification | #21 |
| `ele_m` | `ele` → integer | #9 |
| `lat`, `lon` | node position or `center` | spatial joins |
| `municipality_istat` | point-in-polygon with the municipalities | #22 |
| `wikidata` | as is | linking |

Specific fields:
- `water_points.json`: `drinking`: `true` for `drinking_water` (unless `drinking_water=no`) and for fountains with `drinking_water=yes` or `fountain` = drinking / bubbler; `false` with `drinking_water=no`; else `null` (true 3931, false 10, null 9).
- `cultural_landmarks.json`: `subtype` (original value for the collapsed rare categories, else `null`).
- `guideposts.json`: `on_kept_route` (`true` for the 417 referenced by `guidepost_node_ids` of a kept trail/bike/foot route; the other 89 references point to guideposts outside this file).
- `rest_areas.json`: `osm_id`, `name`, `name_source` (generated "Area di sosta – {municipality}"), `type` (gazebo, picnic_shelter, ...), `lat`, `lon`, `municipality_istat`.
- `_pending_accommodations.json`: `osm_id`, `name`, `type`, `lat`, `lon`, `municipality_istat`.

## Results
- **water_points**: drinking_water 3926, fountain 24; 3824 generated names.
- **cultural_landmarks**: wayside_shrine 1532, wayside_cross 655, ruins 521, memorial 483, military_remains 404, historic_other 229, archaeological_site 179, mine 161, monument 147, attraction 136, castle 104, boundary_stone 81, building 68, fort 55, place_of_worship 55, tomb 20, lime_kiln 18, manor 15, citywalls 15, castle_wall 13, city_gate 11, milestone 6, aqueduct 5, grave_yard 1. Generated names 2918 (mostly unnamed wayside shrines and crosses, kept with a generated label, user decision). wikidata 767.
- **guideposts**: 1352 (417 on a kept route), 802 with `ele`.
- **tourist_info**: office 103, visitor_centre 2.
- **rest_areas**: 268 (gazebo 213, picnic_shelter 49, sun_shelter 2, pavilion 2, picnic_table 1, cabana 1).

## Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `destination*`, `direction_*`, `board_type`, `map_type`, `map_size`, `colour`, `support`, `hiking`, `mtb`, `bicycle` | guidepost/board details |
| `religion`, `denomination`, `memorial`, `military`, `bunker_type`, `resource`, `barrier`, `disused`, `start_date`, `material` | used only for the classification, or not used by any CQ |
| `fountain`, `drinking_water`, `bottle` | summarized in `drinking` |
| `operator`, `access`, `fee`, `wheelchair` | not used by any CQ |
| `check_date`, `source`, `ref`, `description`, `note`, `name:*`, `alt_name`, `wikipedia` | editing metadata, free text, name variants (`wikidata` kept) |

## Checks (all passed)
- `osm_id` unique in each output.
- Every point falls inside a municipality.

## Open points
- The many generated wayside shrines/crosses (2918 generated names in total) weigh a lot in counts like "at least 3 landmarks" (student persona): the query can filter on `name_source = name` if needed.

## Final count
After the cross-file step (`dedup_cross_files.py`, see `cross_file_duplicates.md`): `cultural_landmarks.json` **4910** (4 attractions that duplicate a waterfall or a lake removed).
