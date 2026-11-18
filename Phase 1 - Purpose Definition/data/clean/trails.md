# Cleaning: trails.json

- **Source**: `data/trails.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_trails.py`
- **Outputs**:
  - `data/clean/trails.json`: 1585 trail entities (flat), 1.7 MB (the source is 87 MB)
  - `data/clean/trails_geometry.geojson`: main line of every trail, 17 MB, for the spatial joins (POIs, municipalities, transport, weather) and visual checks. It is not meant to go into the KG as it is.

## Input
1657 `relation` elements with `route=hiking` (1656 `type=route`, 1 `type=superroute`). Members: 34,423 ways with full geometry, 1285 nodes (796 `guidepost`, 9 `board`, the rest unlabeled).

**Key finding**: the way members are referenced as `_fullGeom<id>`, and `<id>` is the OSM way id. All 26,507 distinct way ids match **100%** the ways of `data/ways.json`, so surface/incline/sac_scale of each trail can be derived from `ways.json` later (CQ #2, #3, #7, #15, #16).

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| `type=superroute` | 1 (Sentiero Frassati) | No geometry of its own: it only groups 8 routes, which are kept as normal trails |
| No main way with geometry | 1 (route `438`) | Cannot be placed or measured |
| **Province filter** (see below) | 70 | trails that neither start/end in Trentino nor lie mostly in it |

### Province filter
A trail is considered part of Trentino if **(1) it starts or ends in Trentino, OR (2) at least 50% of its length is in Trentino**.

1. **Start/end rule**: at least one of the two endpoints of the main line falls inside the province polygon. Both endpoints are tested because OSM routes have no reliable direction (`from`/`to` are text, way order is arbitrary). So a trail "starts in Trentino" if it can be started from Trentino. **1574 trails** kept by this rule.
2. **Length rule**: both endpoints are outside, but at least 50% of the main line lies inside the polygon (`length(line ∩ province) / length(line)`, measured in degrees, which is accurate enough for a ratio at this scale). It recovers trails that run almost entirely in Trentino but have both endpoints just across the border. **11 trails** kept by this rule: `460` Vesta – Vesta, `190` Rifugio Revolto – Passo Tre Croci, `234`, `594`, "Malga Camporosà – … – Malga Crojer", three Sentiero Italia stages near the Alto Adige border, "Via Romea - Tratto Trentino", "Alta Via dell'Adamello - Tappa 3", "Ponte Caffaro - Rifugio Stino".

The rule that kept each trail is stored in `province_rule` (`endpoint` or `length_50`). Rule 1 is checked first.

## Changes

### Kept / derived fields
| Output field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"relation/{id}"` (uniform id format `{type}/{id}`, see `README.md`) | key |
| `ref` | `ref` (trail number) | label |
| `reg_ref` | `reg_ref`: SAT cadastre code, `E`/`O` (east/west Trentino) + number, e.g. `E420A` | secondary id |
| `name` | `name`; fallback `"{ref}: {from} – {to}"`, `"Sentiero {ref}"`, `"{from} – {to}"`, `"Trail {osm_id}"` | label |
| `name_source` | `name` 717, `ref_from_to` 735, `ref` 119, `from_to` 6, `osm_id` 8 | provenance |
| `from`, `to` | as is | label, future trailheads |
| `description` | `description`, else `description:it` | text |
| `wikidata` | as is (18 trails) | external linking in the later phases (kept wherever present, user decision) |
| `operator` | normalized list (see below) | – |
| `cai_scale` | base of `cai_scale`: `T`, `E`, `EE`, `EEA` | difficulty |
| `ferrata_grade` | grade after `EEA:` (`F`, `PD`, `MD`, `D`) | #19 |
| `via_ferrata_scale` | as is (22 trails) | #19 |
| `distance_km` | `distance` → float (declared) | #18 |
| `length_km_computed` | geodesic (haversine) length of the main ways | #18 |
| `duration_forward_min`, `duration_backward_min` | `"HH:MM"` → minutes | #8 |
| `ascent_m`, `descent_m` | → integer metres | #1, #6 |
| `ele_from_m`, `ele_to_m`, `ele_max_m`, `ele_min_m` | `ele:*` → integer (~20 trails) | #9 |
| `roundtrip` | `roundtrip` tag; if missing, computed from geometry (see below) | #20 |
| `roundtrip_source` | `tag`, `geometry` or `null` | provenance |
| `province_rule` | `endpoint` or `length_50`: which province rule kept the trail | provenance |
| `start`, `end` | lat/lon of the two endpoints of the main line | #11, #17 |
| `main_way_ids` | `"way/{id}"` of the main ways (roles `""`, `forward`, `backward`), in member order, deduplicated | join with `ways.json` |
| `guidepost_node_ids` | `"node/{id}"` of the node members with role `guidepost` or `board` | join with `guideposts.json` |

### Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `network`, `network:type`, `rwn:name` | not needed by any CQ; long-distance trails can be inferred from other fields |
| `osmc:symbol`, `symbol*`, `colour` | map rendering / trail marks |
| `source*`, `survey:date`, `check_date`, `fixme`, `note*`, `note:project_page`, `website`, `url`, `link` | editing metadata and links |
| `wikipedia`, `wikimedia_commons`, `name:*`, `alt_name*`, `old_*`, `loc_name`, `short_name`, `operator:*` | external links and name variants |
| `importance`, `ref:REI`, `old_ref`, `stage`, `via` | not used by any CQ |
| `foot`, `bicycle`, `mtb`, `hiking`, `pilgrimage`, `religion`, `access`, `oneway`, `sac_scale` and other tags on ≤ 20 relations | rare, not used by any CQ (access/difficulty per segment comes from `ways.json`) |
| ways with roles `alternative`, `alternative:2`, `excursion`, `connection`, `approach` (32 trails) | variants and side trips; excluded so they do not distort length and loop detection |
| way members tagged `building` (2: the buildings of Rifugio Boé and Rifugio Pisciadù in trail 666) | a hut building is not a trail segment: its perimeter was added to the trail length (the huts stay in `huts.json`). The tags come from `ways.json`, because the relation members carry none |

### Transformations
- **Operator normalization**: SAT ("Società degli Alpinisti Tridentini", "SAT"), CAI (all "Club Alpino Italiano …", "CAI …", "C.A.I." sections), AVS (all "Alpenverein Südtirol …"), Parco Naturale Paneveggio - Pale di San Martino (3 spellings), Rete di Riserve Alpi Ledrensi (2), Comune di Limone sul Garda (3). Multi-valued operators (`;` or `,`) become a list. Result: SAT 1134, none 272, CAI 47, Ecomuseo Argentario 35, AVS 15, ...
- **Numbers**: `ascent` "1.692" and "1.550" read as 1692 and 1550 m (`.` as thousands separator). `duration:forward` "5" read as 5 hours (300 min).
- **Geometry**: main ways merged with `linemerge`. 1495 trails merge into a single `LineString`; for the other 90 (gaps or branches) the geometry is a `MultiLineString`, and start/end are the first point of the first way and the last point of the last way (member order).
- **Roundtrip**: the tag wins when present (93). Otherwise, only if the ways merge into one line, `roundtrip = true` when start and end are within 50 m (1418). If the ways do not merge, `roundtrip` is `null` (74). Result: 33 true, 1478 false, 74 unknown.

## Checks (all passed)
- `osm_id` unique.
- Computed vs declared length (1159 trails with both): median ratio 0.970, 87.7% within ±10%, so the geometry and the declared `distance` are consistent.

## Open points
- Derived properties from the segments (% asphalt, max incline, stroller/wheelchair suitability) will be computed after cleaning `ways.json`.
