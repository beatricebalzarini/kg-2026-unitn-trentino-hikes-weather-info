# Cleaning: province_boundaries.json

- **Source**: `data/province_boundaries.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_province_boundaries.py`
- **Outputs**:
  - `data/clean/province.json`: the province as a single flat entity
  - `data/clean/province_boundary.geojson`: the province polygon, used as the spatial filter for all other datasets

## Input
One `relation` (OSM id 45756, `admin_level=6`) with 30 tags and 337 members:
- 170 `way` with role `outer` (21,036 points): the boundary line
- 166 `relation` with role `subarea`: the municipalities
- 1 `node` with role `admin_centre`: Trento

## Changes

### Kept (renamed into a flat schema)
| Output field | Source | Why |
|---|---|---|
| `osm_id` | `"relation/45756"` (uniform id format `{type}/{id}`, see `README.md`) | primary key |
| `name` | `tags.official_name` ("Provincia Autonoma di Trento") | label of the entity |
| `istat` | `tags.ref:ISTAT` ("022") | link key: prefix of the ISTAT codes of all the municipalities |
| `iso3166_2` | `tags.ISO3166-2` ("IT-TN") | standard identifier |
| `wikidata` | `tags.wikidata` ("Q16289") | external linking in the later phases |
| `admin_centre` | `admin_centre` member (`"node/{id}"`, lat, lon) | position of the province |
| `bounds` | `bounds` | fast bounding-box pre-filter |
| `municipality_osm_ids` | `"relation/{id}"` of the 166 `subarea` members | basis for `Municipality partOf Province` |

### Removed
| What | Why |
|---|---|
| Overpass metadata (`version`, `generator`, `osm3s` with timestamps) | not data |
| `name`, `name:*`, `alt_name`, `official_name:*`, `short_name` | not used by any CQ; `official_name` is the only label kept |
| `ref:nuts`, `ref:nuts:2`, `ref:nuts:3` | not used by any CQ |
| `boundary`, `admin_level`, `type` | constant values, implied by the entity type |
| `wikipedia` | redundant with `wikidata` |
| `outer` way geometry | moved to the GeoJSON file (not an attribute of the entity) |

### Geometry
- The 170 `outer` ways are merged and polygonized into **one valid `Polygon`**.
- The polygon is not simplified, because precision near the border matters for the spatial filter.
- Coordinates are in WGS84 (lon, lat), following GeoJSON.

## Checks (all passed)
- Polygon is valid and is a single polygon.
- Trento (`admin_centre`) is inside the polygon.
- All 166 `subarea` ids exist in `municipalities.json`.
- All 165 municipality `admin_centre` nodes fall inside the polygon. One municipality has no `admin_centre`, as noted in `municipalities.md`.
