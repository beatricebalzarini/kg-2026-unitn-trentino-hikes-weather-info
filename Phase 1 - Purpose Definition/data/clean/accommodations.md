# Cleaning: accomodations.json + hotels.json → accommodations.json

- **Sources** (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL):
  - `data/accomodations.json`: 617 elements, `tourism` = guest_house, camp_site, chalet, hostel
  - `data/hotels.json`: 1765 elements, `tourism` = hotel, apartment, motel (second export, made because the first query had no hotels; see `data/hotels.md`)
- **Script**: `cleaning/clean_accommodations.py` (shared POI helpers in `cleaning/poi_common.py`)
- **Other input**: `data/clean/municipalities_boundaries.geojson`
- **Output**: `data/clean/accommodations.json`: **2348** accommodations, one file for both sources (the file name is spelled correctly, with two "m")

## Input
- `accomodations.json`: 248 `node`, 363 `way`, 6 `relation`; `tourism`: guest_house 407 (subtypes bed_and_breakfast 58, agritourism 35, guest_house 3, hotel 2, apartment 2), camp_site 99, chalet 94, hostel 17.
- `hotels.json`: 857 `node`, 901 `way`, 7 `relation`; `tourism`: hotel 1380, apartment 381, motel 4.
- Positions: `lat`/`lon` for nodes, `center` for ways and relations. All 2382 elements are inside the province. No OSM id is in both sources.

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| Outside the province polygon | 0 | all inside. The structures on Lake Garda (Riva del Garda, Nago-Torbole) are inside Trentino and kept (user decision; the original todo said "delete lake garda") |

## Merging duplicates
**Rule (user decision)**: elements with the **same name** (case-insensitive), the **same category** and **all within 200 m of each other** are the same structure and are merged. It is applied to **both sources together**. It covers a structure mapped twice (typically as a point and as a building) and the units of one holiday village mapped one by one.

The kept entity takes the smallest `osm_id` of the group, the **centroid** of the elements as position (and its municipality), `unit_count` = number of elements, `merged_osm_ids` = all the OSM ids, and any field missing in the kept element is filled from the others.

- **25 groups merged, 34 elements fewer**: hotel 11, apartment 5, guest_house 4, chalet 3, camp_site 2.
- Largest: "villaggio - bungalow val Molini" (9 elements), "Bungalow al Lago" (3), "Condominio Meledrio" (3). Farthest apart: "Camping Val Malene" (144 m), "villaggio - bungalow val Molini" (70 m), "Sporthotel Rosatti Eurotour" (61 m), "Villa Stella" (58 m).
- Examples of point + building: "Albergo Dimaro", "Hotel Compet", "Park Hotel Azalea", "Residence Montebel", "B&B Angela", "Camping Moser", "Malga Vallorsara".
- **92 same-name groups are not merged** because they are farther than 200 m: different places with the same name (e.g. "Hotel Paganella" 5.3 km, "Camping Al Lago" 9.6 km, "La Villa" 24.6 km), or chains.

## Overlaps with the other datasets
- **`amenities.json`**: 93 objects (20 guest houses/agritourisms + 73 hotels with a restaurant or bar) have the same `osm_id` and identical tags. They are kept **only here**, with `food_service = true` and `cuisine`, and excluded from `food_drink.json` (user decision, same as the huts).
- **`mixed_pois.json`**: 9 objects (5 hotels, 4 guest houses) are excluded there because they are here. The 4 hotels that were parked in `_pending_accommodations.json` are now here, so that file is empty.

## Output fields
| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"{type}/{id}"` (smallest id for merged groups) | key |
| `name` | `name`; if missing, generated `"{type} – {municipality}"` (e.g. "Campeggio – Levico Terme", "Hotel – Canazei"), 76 | label |
| `name_source` | `name` or `generated` | provenance |
| `category` | one category: the `guest_house=*` subtype when it is bed_and_breakfast / agritourism / hotel / apartment, else `tourism`. Result: hotel 1371, apartment 376, guest_house 306, camp_site 97, chalet 84, bed_and_breakfast 58, agritourism 35, hostel 17, motel 4 | #5 |
| `source_dataset` | `accomodations.json` (601) or `hotels.json` (1747) | provenance |
| `stars` | integer, the leading digit (user decision): `3S` ("superior") → 3, `4S` → 4, `3.5` → 3, `4-5` → 4. Result: 1★ 7, 2★ 44, 3★ 369, 4★ 112, 5★ 5 (537 filled) | – |
| `rooms` | → integer (53) | – |
| `capacity` | `capacity`, else `beds` → integer (12) | #5 |
| `capacity_source` | `capacity`, `beds` or `null` | provenance |
| `capacity_pitches`, `tents`, `caravans`, `motorhome` | only for `camp_site`: integer and booleans (23, 82, 85, 67) | – |
| `wheelchair` | `yes` / `limited` / `no` (164) | elderly/disabled persona |
| `dog` | `yes`/`leashed` → true, `no` → false (64) | – |
| `internet_access` | `yes`/`wlan`/`wired` → true, `no` → false (first value if multi-valued) (332) | – |
| `food_service` | **true only if a tag says so** (`cuisine`, or `amenity` = restaurant / bar / cafe / fast_food / pub), else `null` = not verified (108 true) | #4 |
| `food_service_source` | `tag` or `null` | provenance |
| `cuisine` | list, as in `food_drink.json` (57) | #4 |
| `opening_hours` | as is (24) | – |
| `operator` | list, same normalization as the huts; names of private persons kept (public OSM data, user decision) (133) | – |
| `ele_m` | `ele` → integer (36) | #9 |
| `lat`, `lon` | node position or `center`; centroid for merged groups | spatial joins |
| `municipality_istat` | point-in-polygon with the municipalities | #22 |
| `phone` | list from `phone` + `contact:phone` + `contact:mobile` + `mobile`, normalized as for the huts (948) | contacts |
| `email`, `website` | `email`/`contact:email` (lowercased), `website`/`contact:website` (706, 1066) | contacts |
| `wikidata` | as is (56) | linking |
| `unit_count`, `merged_osm_ids` | 1 / `null`, except the 25 merged groups | provenance |

## Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `fee` | always `yes` in `accomodations.json`: no information |
| `addr:*`, `noaddress` | partial and inconsistent; the municipality comes from the coordinates |
| `ref:vatin`, `ref:cin` | official references (user todo) |
| `check_date`, `source`, `building*`, `roof:*` | editing metadata, building details |
| `fax`, `contact:fax`, `contact:facebook`, `contact:whatsapp` and other social links | not used by any CQ |
| `internet_access:fee`, `smoking`, `air_conditioning`, `outdoor_seating`, `bar` | hotel services not used by any CQ |
| `power_supply`, `sanitary_dump_station`, `shower`, `toilets`, `drinking_water`, `static_caravans`, `cabins` | camping services not used by any CQ |
| `guest_house` | merged into `category` |
| `name:*`, `alt_name`, `description`, `note`, `wikipedia` | name variants and free text (`wikidata` kept) |

## Checks (all passed)
- `osm_id` unique; no OSM id in both sources.
- Every accommodation falls inside a municipality.

## Final count
After the cross-file step (`dedup_cross_files.py`, see `cross_file_duplicates.md`): **2347** (1 duplicate of a hut removed; 41 duplicates absorbed from `food_drink.json`, listed in `duplicates`).
