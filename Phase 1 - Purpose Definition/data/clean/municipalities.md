# Cleaning: municipalities.json

- **Source**: `data/municipalities.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_municipalities.py`
- **Outputs**:
  - `data/clean/municipalities.json`: 166 municipality entities (flat), sorted by ISTAT code
  - `data/clean/municipalities_boundaries.geojson`: one polygon per municipality, used to assign trails/POIs/weather to a municipality (CQ #22 "weather for zone X")

## Input
166 `relation` elements (`admin_level=8`), one per municipality of the Autonomous Province of Trento:
- 11 tags present in every relation, plus 28 rare tags (names in other languages, coat of arms, flag, ...)
- 1275 `outer` and 3 `inner` way members (93,332 points), 165 `admin_centre` nodes, 45 `label` nodes

Correction to `data/municipalities.md`: the largest municipality has 119,953 inhabitants (Trento), not 10,422.

## Changes

### Kept (flat schema)
| Output field | Source | Why |
|---|---|---|
| `istat` | `tags.ref:ISTAT` | **primary key** (6 digits, prefix `022`); shared with other open data |
| `osm_id` | `"relation/{id}"` (uniform id format `{type}/{id}`, see `README.md`) | link with `province.json` (`municipality_osm_ids`) |
| `name` | `tags.name` | label (all 166 names are unique) |
| `province_istat` | constant `"022"` | relation `Municipality partOf Province` |
| `postal_code` | `tags.admin_centre:postal_code` | to find a "zone X" by postal code |
| `wikidata` | `tags.wikidata` | external linking in the later phases |
| `centre` | `admin_centre` member (lat, lon) | reference point for weather and "near me" queries |
| `centre_source` | `admin_centre` or `polygon_centroid` | provenance of `centre` |
| `bounds` | `bounds` | fast bounding-box pre-filter |

### Removed
| What | Why |
|---|---|
| Overpass metadata (`version`, `generator`, `osm3s` with timestamps) | not data |
| `population`, `population:date`, `source:population` | not used by any CQ |
| `ref:catasto` | tax/cadastral code, not used by any CQ; ISTAT is the key |
| `name:*`, `alt_name*`, `old_name*`, `official_name`, `short_name`, `reg_name` | name variants, not used by any CQ (same choice as for the province) |
| `wikipedia`, `wikimedia_commons` | redundant with `wikidata` |
| `admin_level`, `boundary`, `type` | constant values, implied by the entity type |
| `gfoss_id`, `coat_of_arms`, `flag`, `natural` | present in 1-2 municipalities, not relevant |
| `label` nodes | only a map rendering hint |
| boundary way geometry | moved to the GeoJSON file |

### Transformations
- **Mori** has no `admin_centre` member: its `centre` is the **centroid of its polygon** (45.856413, 10.951497), with `centre_source = "polygon_centroid"`.
- Geometry: `outer` ways merged and polygonized, `inner` rings (3 in total) subtracted as holes. Result: 143 `Polygon` and 23 `MultiPolygon` (municipalities with exclaves). Not simplified. WGS84 (lon, lat).

## Checks (all passed)
- All 166 geometries are valid and not empty.
- ISTAT codes are unique and all start with `022`.
- Every `centre` falls inside its own municipality polygon (including Mori's centroid).
- The union of the 166 municipalities coincides with the province polygon (symmetric difference ≈ 0% of the area).
