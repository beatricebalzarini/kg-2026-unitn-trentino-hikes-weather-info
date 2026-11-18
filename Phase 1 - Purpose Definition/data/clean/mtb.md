# Cleaning: mtb.json

- **Source**: `data/mtb.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_mtb.py` (shared helpers in `cleaning/route_common.py`, same rules as `clean_trails.py`)
- **Outputs**:
  - `data/clean/mtb.json`: 134 bike routes (85 `mtb`, 49 `bicycle`), 222 KB
  - `data/clean/mtb_geometry.geojson`: main line of every route, 3.4 MB, for the spatial joins

## Input
144 `relation` elements, all `type=route`: `route=mtb` 91 (mountain-bike trails) and `route=bicycle` 53 (cycle paths, "ciclovie"). Members: 12,833 ways with empty role, 1137 `forward`, 487 `backward`, 49 `guidepost` nodes. All routes have geometry.

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| `state=proposed` | 2 ("Via Claudia Augusta" VCA, note "not yet signposted"; "Limarò - Preore") | Planned routes, not yet signposted on the ground: they must not be returned as cyclable routes. The roads exist, but the itinerary does not. |
| **Province filter** (same as `trails.json`): kept if **(1) it starts or ends in Trentino, OR (2) at least 50% of its length is in Trentino** | 8 | outside Trentino |

Kept by rule 1 (`endpoint`): 130. Kept by rule 2 (`length_50`): 4.

## Output fields
| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"relation/{id}"` (uniform id format `{type}/{id}`, see `README.md`) | key |
| `kind` | `route`: `mtb` or `bicycle` | #10 |
| `ref`, `from`, `to`, `description` | as is | label / text |
| `wikidata` | as is (5 routes) | external linking in the later phases (kept wherever present, user decision) |
| `name` | see "Labels" below | label |
| `name_source` | `name` 78, `name_stage` 23, `ref` 13, `ref_from_to` 10, `from_to` 5, `osm_id` 5 | provenance |
| `operator` | list, same normalization as the trails (SAT / CAI / AVS); here no variant needed merging | – |
| `cai_scale_mtb` | `cai_scale:mtb`: CAI MTB difficulty scale (`MC` 21, `OC` 2) | #10 |
| `mtb_scale` | `mtb:scale` → 0–6 (8 routes) | #10 |
| `distance_km` | `distance`, or `length` when `distance` is missing (2 routes) → float | #18 |
| `distance_source` | `distance`, `length` or `null` | provenance |
| `length_km_computed` | geodesic length of the main ways | #18 |
| `ascent_m`, `descent_m` | → integer (8 and 5 routes only) | #1, #6 |
| `roundtrip`, `roundtrip_source` | same rule as the trails: tag first, else geometry only if the ways merge into one line (50 m tolerance), else `null` | #20 |
| `province_rule` | `endpoint` or `length_50` | provenance |
| `start`, `end` | endpoints of the main line | #11, #17 |
| `main_way_ids` | `"way/{id}"` of the ways with role `""`, `forward`, `backward` → join with `ways.json` | segments |
| `guidepost_node_ids` | `"node/{id}"` of the `guidepost`/`board` node members (49) | join with `guideposts.json` |

### Labels
Same fallbacks as the trails, with two differences:
- the 23 stages of "SICAI Ciclo" (ref `SI-C`) all have the same `name`, so the stage is appended: `"SICAI Ciclo – Tappa B01-A"`. `stage` is used only for the label and is not kept as a field (as for the trails);
- routes with only a `ref` get `"Percorso MTB {ref}"` or `"Percorso ciclabile {ref}"` (e.g. the "bicipolitana" lines of Trento), not `"Sentiero {ref}"`.

After this, no two routes share the same name.

## Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `network`, `cycle_network` | not needed by any CQ (same choice as the trails) |
| `stage`, `date` | stage info, not used by any CQ (stage only used in the label) |
| `oneway`, `mtb:type`, `cai_scale:mtb:uphill`, `mtb:scale:imba` | not used by any CQ, or rare |
| `colour`, `osmc:symbol`, `website`, `source`, `note*`, `fixme`, `state` | rendering and editing metadata |
| `wikipedia*`, `name:*`, `alt_name`, `loc_name`, `official_name`, `mtb:name`, `operator:*`, `importance`, `ref:bz.it` | external links and name variants |
| `bicycle`, `foot`, `local`, `trail_visibility`, `via`, `signed_direction` | single occurrences |

## Results
- 134 routes: 85 `mtb`, 49 `bicycle`.
- Geometry: 78 merge into one `LineString`, 56 stay `MultiLineString`. Bike routes often have separate `forward`/`backward` ways, or gaps, which do not merge into one line.
- Roundtrip: 11 true, 81 false, 42 unknown (because of the 56 unmerged geometries).

## Checks
- `osm_id` unique; names unique.
- Computed vs declared distance (25 routes): median ratio 0.997, 76% within ±10%. The 6 outliers are OSM data issues, kept as they are:
  - incomplete relations (fewer ways mapped than the declared length): "Percorso MTB 207" (3.2 vs 28.4 km), "Ciclovia Valle del Chiese CV-TN07" (32.8 vs 42.8), "Ciclovia della Val Rendena" (23.3 vs 26.4), "diramazione Rotaliana" (4.3 vs 6.0);
  - longer computed length: "MTB: Latemar Tour" (52.8 vs 38.0, the `forward` and `backward` ways are both counted), "Pista Ciclabile Taio - Sabino" (8.2 vs 7.0, from `length`).

## Open points
- `distance` is declared on only 25 routes and `ascent` on 8: CQ #18 will rely on `length_km_computed`, and CQ #1/#6 (height difference) for bike routes need a DEM.
- Segment-level data (surface, mtb_scale per way, ...) come from `full_stroller_mtb.json` (step 7).
