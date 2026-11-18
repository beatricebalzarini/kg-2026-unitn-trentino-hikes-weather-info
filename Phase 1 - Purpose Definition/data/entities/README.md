# data/entities — one file per entity type (ER model)

The final data of Phase 1: **one JSON file per entity type** of the ER model (`../../ER-model.md`), built from the cleaned files in `../clean/` by `cleaning/build_entities.py` (last steps of `cleaning/run_all.py`). OSM data © OpenStreetMap contributors, ODbL.

**`dem.md`** documents the elevation enrichment with the Copernicus DEM (missing elevations, ascent/descent, `max_incline_pct`), with its validation in `dem_validation.json`.

**`SCHEMA.md`** describes every file and every field (type, how often it is filled, values, meaning) and the references between files. It is generated from the data by `cleaning/schema_report.py`, so it always matches the files.

| File | EType | Entities |
|---|---|---|
| `routes.json` (+ `routes_geometry.geojson`) | Route | 1757 |
| `segments.json` | Segment | 26,047 |
| `landmarks.json` (+ `landmarks_geometry.geojson`, lake and glacier polygons) | Landmark | 9523 |
| `hospitality.json` | Hospitality | 5698 |
| `facilities.json` | Facility | 6026 |
| `transport.json` | Transport | 3985 |
| `municipalities.json` (+ `municipalities_boundaries.geojson`) | Municipality | 166 |
| `province.json` (+ `province_boundary.geojson`) | Province | 1 |
| **total** | | **53,203** |

## Uniform schema
- Every row of a file has the **same fields in the same order**; `null` = not applicable or not known.
- `id` first: `{osm type}/{osm id}` (ISTAT code for municipalities and the province, `via_ferrata/<slug>` for the rebuilt via ferrata). It will be the entity URI.
- Then `name`, `name_source` (`name`, `name_stage`, `name_disambiguated`, `ref_from_to`, `ref`, `from_to`, `generated`), `name_osm` (the OSM name tag) and `category` (the subtype).
- Position: `lat`/`lon` for points, `start`/`end` (+ line geometry) for routes.
- `municipality_istat` (or `municipalities_istat` for landmarks, since a lake can touch several municipalities) → `municipalities.id`.
- Provenance last: `wikidata`, `source_dataset` (raw OSM export), `merged_osm_ids` (`[{osm_id, file}]` of the other OSM objects merged into the entity); every inferred value has a `*_source` field; `ele_source = "tag"`.

## What changed with respect to `../clean/`
| Change | Why |
|---|---|
| trails + mtb + foot_routes + via_ferrata → `routes.json`, `category` = trail / mtb / bicycle / foot / via_ferrata | one Route EType |
| landmarks + lakes + glaciers + cultural_landmarks → `landmarks.json`, `landmark_type` = natural / cultural | one Landmark EType (lakes and glaciers are landmarks) |
| huts (alpine/wilderness) + accommodations + food_drink → `hospitality.json`, with `overnight` and `food_service` | CQ #4 and #5 become two attributes of one EType |
| water_points + rest_areas + guideposts + tourist_info + emergency shelters → `facilities.json` | services along the way; emergency shelters are not hospitality |
| transport_stops + aerialways → `transport.json`, `category` = bus_stop, bus_station, train_station, funicular_station, lift_station, chair_lift, gondola, cable_car, lift_unknown | one Transport EType |
| `osm_id` → `id`; `main_way_ids` → `segment_ids`; `guidepost_node_ids` → `guidepost_ids`; `length_km_computed` → `length_km`; municipality `centre` → `lat`/`lon`; `province_istat` → `province_id` | uniform names |
| `name_source` values unified (`osm` → `name`, `osm_basin`/`osm_part`/`osm_municipality` → `name_disambiguated`, `osm_id` → `generated`); `name_osm` added everywhere | one vocabulary |
| `merged_osm_ids` (same file) and `duplicates` (other files) → one `merged_osm_ids` list of `{osm_id, file}`, without the entity's own id | one field |
| `ele_source`, `source_dataset` added everywhere; segment `stroller` yes/no → boolean; food & drink places get `food_service = true` (`food_service_source = category`) and `overnight = false` | uniform provenance and types |

Elevations: every missing elevation, ascent/descent and `max_incline_pct` are filled from the Copernicus DEM (`dem.md`); OSM tags always win.

Not computed yet (integration step): the derived Route attributes (`paved_pct`, `stroller_suitable`, `wheelchair_suitable`) and the spatial relationships (`passesBy`, `nearTo`, `startsNear`, `crosses`, `hasStation`).
