# Cleaning: public_transportation.json → transport_stops.json + aerialways.json

- **Source**: `data/public_transportation.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_public_transport.py` (shared POI helpers in `cleaning/poi_common.py`)
- **Other inputs**: `data/clean/_pending_bus_shelters.json` (from `clean_huts_landmarks.py`), `data/clean/municipalities_boundaries.geojson`, `data/clean/ways.json` (only for a check)
- **Outputs**:
  - `data/clean/transport_stops.json`: **3781** places where you board a means of transport (bus, train, funicular, lifts)
  - `data/clean/aerialways.json`: **204** lift lines (chair lifts, gondolas, cable cars)
  - `data/clean/_unmatched_bus_shelters.json`: 42 bus shelters that could not be matched to a stop (kept for reference, not used)

## Input
4948 elements: 4624 `node`, 322 `way`, 2 `relation` (position from `center`). 4940 inside the province. 4470 have a name.
Bus stops (`highway=bus_stop` and platforms) ~4056, bus stations 19, railway stations/halts 71 (+ 8 generic `public_transport=station`, 2 funiculars), lift stations 582, lift lines 212. The lift lines have **only a `center`**, no geometry.

## Classification
| Rule (first that matches) | Output | `mode` / `kind` or `type` |
|---|---|---|
| `aerialway=station` | stops | `aerialway` / `station` |
| `aerialway` = chair_lift, gondola, cable_car, (mixed_lift, drag_lift, ...), `yes` | aerialways | that value (`yes` → `unknown`) |
| `station=funicular` | stops | `funicular` / `station` |
| `railway` = station, halt; or `station=train`; or `train=yes` | stops | `train` / `station` |
| `amenity=bus_station`, or `public_transport=station` (no railway tag) | stops | `bus` / `station` |
| `highway=bus_stop*`, or `public_transport` = platform, stop_position | stops | `bus` / `stop` |

Lift stations are included among the stops (user decision): in summer many lifts take hikers up, which matters for CQ #11 ("reachable by public transport").

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| Outside the province polygon | 8 | consistency with the other files (user decision). A stop just across the border could serve a border trail: accepted |

## Pending bus shelters → `has_shelter`
The 203 bus shelters parked by the huts step (`amenity=shelter` + `shelter_type=public_transport`) are the roofs of bus stops. Each one is assigned to the **nearest bus stop within 30 m**, **excluding stops explicitly tagged `shelter=no`** (an explicit tag is respected).
- matched: 161 (42 of them added a shelter to a stop that had no `shelter` tag; the others confirmed `shelter=yes`);
- unmatched: 42 (no eligible stop within 30 m) → `_unmatched_bus_shelters.json`.

## Merging stops (user decision)
Stops with the **same name**, the **same mode**, and linked by distances **≤ 100 m** (single-linkage: A–B ≤ 100 m and B–C ≤ 100 m → one group) are **one stop**: typically the two platforms on the two sides of a road, or the platforms of a bus station.
- 935 groups, 955 elements merged away (bus 917 groups, aerialway stations 17, train 1). Largest: "Riva del Garda - Autostazione" (9 elements).
- The merged stop takes: the smallest `osm_id` (a station is preferred over a platform), the **centroid** as position (and its municipality), `kind = station` if any element is a station, `has_shelter` = true if any element has one (else false if any says no, else null), the best `wheelchair` value (yes > limited > no), missing fields filled from the others, and `merged_osm_ids` = all the OSM ids.
- Unnamed stops are not merged.

## Output fields

### `transport_stops.json`
| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"{type}/{id}"` | key |
| `name` | `name`; if missing, generated "Fermata bus – {municipality}", "Stazione impianto – …", ... (471) | label |
| `name_source` | `name` or `generated` | provenance |
| `mode` | `bus` 3149, `aerialway` 562, `train` 68, `funicular` 2 | #11 |
| `kind` | `stop` / `station` | #11 |
| `operator` | list, normalized: every Trentino Trasporti spelling ("Trentino trasporti S.p.A.", "TTesercizio", "Trentino Trasporti (linea 204)", ...) → `Trentino Trasporti`; Dolomitibus → `DolomitiBus`; Rete Ferroviaria Italiana → `RFI`; values that are only a bus line ("Linea 101") dropped | – |
| `has_shelter` | `shelter` yes/separate → true, no → false; plus the matched pending shelters (true 663, false 1095, null 2023) | – |
| `has_shelter_source` | `tag` or `pending_bus_shelter` | provenance |
| `wheelchair` | `yes` / `limited` / `no` (324) | elderly/disabled persona |
| `summer_access` | only lift stations: `aerialway:summer:access` (`no` 82, `both` 35, `exit` 2, `entry` 1) | #11 (lifts usable in summer) |
| `ele_m` | `ele` → integer | – |
| `lat`, `lon` | node position or `center`; centroid for merged stops | spatial joins (#11) |
| `municipality_istat` | point-in-polygon with the municipalities | #22 |
| `wikidata` | as is | linking |
| `merged_osm_ids` | all OSM ids of a merged stop, else `null` | provenance |

### `aerialways.json`
| Field | Source / transformation |
|---|---|
| `osm_id`, `name`, `name_source` | generated "Impianto – {municipality}" if unnamed (7) |
| `type` | chair_lift 137, gondola 51, cable_car 13, unknown 3 |
| `duration_min` | `aerialway:duration` → minutes; `"7:10"` = 7 min 10 s → 7.17 (77 filled) |
| `summer_access` | `aerialway:summer:access` (only 2 lines; the value is usually on the stations) |
| `operator`, `lat`, `lon` (`center`), `municipality_istat`, `wikidata` | as for the stops |

4 of the 13 lifts that are segments of bike routes (`ways.json`, field `aerialway`) are also in `aerialways.json` (same OSM way id).

## Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `aerialway:occupancy`, `aerialway:capacity` | seats and hourly capacity: not used by any CQ (user decision) |
| `aerialway:heating`, `aerialway:bubble`, `aerialway:access`, `aerialway:station` | lift details not used by any CQ |
| `bench`, `bin`, `lit`, `tactile_paving`, `departures_board`, `check_date*`, `internet_access` | stop furniture |
| `bus`, `train`, `railway`, `highway`, `public_transport`, `amenity`, `station` | used only for the classification |
| `network`, `route_ref`, `ref` | lines and networks: not used by any CQ |
| `source`, `note`, `building`, `wikipedia`, `name:*`, `alt_name`, `oneway`, `bicycle` | editing metadata, building details, name variants (`wikidata` kept) |

## Checks (all passed)
- `osm_id` unique in each output.
- Every stop and line falls inside a municipality.

## Open points
- Lift lines have no geometry: the link "lift line → its stations" can only be done by distance, if needed.
- Most stops have no `operator` (3275 of 3781).
