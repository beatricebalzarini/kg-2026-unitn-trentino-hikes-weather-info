# data/clean — cleaned OSM datasets (Phase 1)

> These files are the intermediate step of the pipeline. The final data, **one file per entity type of the ER model**, is in `../entities/` (see `../entities/README.md` and `../entities/SCHEMA.md`).

Cleaned versions of the OpenStreetMap exports in `../` (OSM data © OpenStreetMap contributors, ODbL). The originals are never modified. Every output has a `.md` that documents what was kept, removed and transformed, and why. Open questions are in `OPEN_ISSUES.md`. The weather data is handled separately (not in this folder).

## How to rebuild
From the repository root:
```
.venv/bin/python "Phase 1 - Purpose Definition/cleaning/run_all.py"
```
It runs the 16 steps in order (the last two build `../entities/` and its `SCHEMA.md`) (several scripts read the outputs of the previous ones), checks the result and writes the hash of every output in `cleaning/last_run_hashes.json`. **Two consecutive runs give identical outputs** (checked). Requirements: `shapely`, `pyproj` (installed in `.venv`). Shared rules (distances, operator normalization) are in `cleaning/normalize.py`; route and POI helpers in `cleaning/route_common.py` and `cleaning/poi_common.py`.

**Always rebuild with `run_all.py`**: running a single script alone can leave the files inconsistent (e.g. `clean_mixed_pois.py` rewrites files that `dedup_cross_files.py` then corrects).

## Conventions (all files)
- **Ids**: `"{type}/{id}"` with the OSM element type: `relation/129319` (routes, municipalities, province), `way/4699598` (segments, polygons), `node/123` (points). OSM ids are unique only together with the type, and the id will become the entity URI in the KG. The only non-OSM ids are the via ferrata rebuilt from several ways: `via_ferrata/<slug>`. References use the same format (`main_way_ids`, `guidepost_node_ids`, `municipality_osm_ids`, `merged_osm_ids`, `duplicates`).
- **Municipality**: `municipality_istat` (or `municipalities_istat` for lakes/glaciers) = 6-digit ISTAT code, key of `municipalities.json`.
- **Provenance**: every derived or inferred value has a `*_source` field (`name_source`, `roundtrip_source`, `surface_source`, `food_service_source`, ...). Values not stated by a tag are left `null` (= not verified), never guessed.
- **Generated labels**: unnamed objects get `"{type} – {municipality}"` with `name_source = "generated"`.
- **`wikidata`**: kept on every entity where present (not on way segments).
- **Geometry**: lines and polygons are in separate `*_geometry.geojson` files (WGS84), the JSON files only carry points.
- **Duplicates**: the same object is one entity. Merges inside a file are listed in `merged_osm_ids`; duplicates removed from another file in `duplicates` (see `cross_file_duplicates.md`). The same OSM object with two roles (e.g. a lift that is also a route segment) keeps the same id in both files and becomes one KG entity with two types (`_shared_objects.json`).

## Files
| File | Entities | Source | Doc |
|---|---|---|---|
| `province.json` + `province_boundary.geojson` | 1 | province_boundaries.json | `province_boundaries.md` |
| `municipalities.json` + `municipalities_boundaries.geojson` | 166 | municipalities.json | `municipalities.md` |
| `trails.json` + `trails_geometry.geojson` | 1585 | trails.json | `trails.md` |
| `mtb.json` + `mtb_geometry.geojson` | 134 | mtb.json | `mtb.md` |
| `foot_routes.json` + `foot_routes_geometry.geojson` | 12 | stroller.json | `foot_routes.md` |
| `via_ferrata.json` + `via_ferrata_geometry.geojson` | 26 | via_ferrata_routes.json | `via_ferrata.md` |
| `ways.json` | 26,047 | ways.json, full_stroller_mtb.json, via_ferrata_routes.json | `ways.md`, `full_stroller_mtb.md` |
| `huts.json` | 745 | huts_landmarks.json | `huts_landmarks.md` |
| `landmarks.json` | 4386 | huts_landmarks.json | `huts_landmarks.md` |
| `accommodations.json` | 2347 | accomodations.json, hotels.json | `accommodations.md` |
| `food_drink.json` | 2957 | amenities.json | `food_drink.md` |
| `lakes.json` + `lakes_geometry.geojson` | 160 | lakes_geom.json | `lakes.md` |
| `glaciers.json` + `glaciers_geometry.geojson` | 67 | lakes_geom.json | `lakes.md` |
| `water_points.json` | 3950 | mixed_pois.json | `mixed_pois.md` |
| `cultural_landmarks.json` | 4910 | mixed_pois.json | `mixed_pois.md` |
| `guideposts.json` | 1352 | mixed_pois.json | `mixed_pois.md` |
| `tourist_info.json` | 105 | mixed_pois.json | `mixed_pois.md` |
| `rest_areas.json` | 268 | huts_landmarks.json | `mixed_pois.md` |
| `transport_stops.json` | 3781 | public_transportation.json (+ bus shelters) | `public_transportation.md` |
| `aerialways.json` | 204 | public_transportation.json | `public_transportation.md` |
| **Total** | **53,202** | | |

Not used: `singular_paths.json` (`singular_paths.md`), `trailheads.json` (`trailheads.md`), `lakes.json` (replaced by `lakes_geom.json`), `parking.json` (on hold, `../parking.md`).

Technical files: `_pending_bus_shelters.json`, `_pending_rest_areas.json` are intermediate files between steps (`_pending_accommodations.json` is no longer written: nothing is pending since the hotels were added); `_unmatched_bus_shelters.json` (42 shelters with no stop); `_shared_objects.json` (13 objects with two roles).
