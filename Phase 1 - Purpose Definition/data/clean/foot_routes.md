# Cleaning: stroller.json → foot_routes.json

- **Source**: `data/stroller.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_stroller.py` (shared helpers in `cleaning/route_common.py`, same rules as `clean_trails.py`)
- **Outputs**:
  - `data/clean/foot_routes.json`: 12 walking routes, `kind = "foot"`
  - `data/clean/foot_routes_geometry.geojson`: main line of every route

## Input
13 `relation` elements, all `route=foot`, with 553 way members (with geometry) and 56 node members.

## Why the output is renamed and has no "stroller" flag
The source file is called `stroller.json`, but **nothing in the data says these routes are stroller-friendly**. The stroller filter existed only in the name of the Overpass query. Checking the 13 routes and the tags of their segments (from `full_stroller_mtb.json`):

- all 13 are generic `route=foot` relations: urban trekking in Trento, thematic and educational paths, a Via Crucis;
- **no segment has a `stroller` tag**, and none has `wheelchair`;
- several routes are clearly **not** suitable for a stroller:
  - steps (`highway=steps`) in "Percorso tematico Paoarhoff", "Intrighi e misteri ai tempi del Concilio" and "Percorso ciclo-pedonale Quota 860";
  - only dirt paths in "Sentiero geologico Antonio Stoppani" (`highway=path`, `surface=dirt`);
  - mostly a main road in "Vecchia Gardesana" (142 of 259 ways are `highway=primary`).

So a `stroller_friendly = true` flag would be false. The routes are kept as **generic walking routes** (`kind = "foot"`), and the output file is named `foot_routes.json` so that the name does not suggest a verified stroller suitability. Stroller and wheelchair suitability (CQ #3, #15) will be computed later **from the segments** (surface, smoothness, steps, width, sac_scale), in the same way for all route kinds (trails, mtb, foot).

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| No way member | 1 ("Folgaria - La cultura fa centro", id 14460844) | No geometry: it cannot be placed or measured |
| **Province filter** (same as `trails.json`): kept if (1) it starts or ends in Trentino, OR (2) at least 50% of its length is in Trentino | 0 | all 12 routes start or end in Trentino (`province_rule = endpoint`) |

## Output fields
Same schema as `trails.json` and `mtb.json`, without the fields that no foot route has (no `distance`, `duration`, `ascent`, `descent`, difficulty or `ele:*` tag in the source).

| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"relation/{id}"` (uniform id format `{type}/{id}`, see `README.md`) | key |
| `kind` | constant `"foot"` | route type |
| `ref`, `from`, `to`, `description` | as is (present on 1–2 routes) | label / text |
| `wikidata` | as is (2 routes: "Sentiero geologico Antonio Stoppani", "Via Crucis di Laghel") | external linking (kept wherever present, user decision) |
| `name` | `name` (12 of 13); fallback `"Percorso {ref}"`, `"{from} – {to}"`, `"Percorso a piedi {osm_id}"` | label |
| `name_source` | `name` 11, `osm_id` 1 | provenance |
| `operator` | list (2 routes: "APT Trento, Monte Bondone, Valle dei Laghi" kept as one operator, "Comune di Imèr"). `;` always separates operators, `,` only when every part starts with "Comune di" | – |
| `length_km_computed` | geodesic length of the main ways | #18 |
| `roundtrip`, `roundtrip_source` | tag first, else geometry only if the ways merge into one line (50 m tolerance), else `null` | #20 |
| `province_rule` | `endpoint` | provenance |
| `start`, `end` | endpoints of the main line | #11, #17 |
| `main_way_ids` | `"way/{id}"` of the ways with role `""`, `forward`, `backward` → join with `ways.json` | segments |
| `guidepost_node_ids` | `"node/{id}"` of the `guidepost`/`board` node members | join with `guideposts.json` |

Missing values are left as `null` (unknown). Length, height difference, slope and duration will be filled in a single enrichment step after all the files are cleaned (to be decided).

## Removed
| What | Why |
|---|---|
| Overpass metadata (timestamps) | not data |
| `route`, `type` | constant, replaced by `kind` |
| `network`, `network:type` | not needed by any CQ (same choice as the trails) |
| `website`, `url`, `wikipedia` | external links (`wikidata` is kept) |
| way members tagged `building` (1: Santuario della Madonna di Làghel, in "Via Crucis di Laghel") | a building is not a route segment (same rule as the trails, tags from `full_stroller_mtb.json`) |
| `historic`, `roundtrip` of the dropped route | belonged to the dropped Folgaria route only |

## Results
| osm_id | Name | Length (km) | Roundtrip |
|---|---|---|---|
| 141164 | Intrighi e misteri ai tempi del Concilio | 2.246 | unknown |
| 7464411 | Itinerario 1 Colline Avisiane | 1.634 | no |
| 8729563 | Percorso tematico Paoarhoff. La fattoria della lana | 0.136 | no |
| 10097020 | Il Bosco Nascosto - Percorso Lungo (Blu) | 4.008 | yes |
| 12079333 | Giro dei Masi | 6.144 | no |
| 13698494 | Percorso a piedi 13698494 (no name in OSM) | 0.273 | no |
| 14450261 | connessione a SAT O281 | 0.722 | no |
| 17583186 | Sentiero geologico Antonio Stoppani | 1.167 | unknown |
| 18633332 | Percorso ciclo-pedonale Quota 860 | 32.758 | yes |
| 19376694 | Percorso Sensoriale "Immèrgiti" | 0.578 | no |
| 21037232 | Vecchia Gardesana | 30.894 | unknown |
| 21416947 | Via Crucis di Laghel | 0.577 | no |

Geometry: 9 merge into one line, 3 do not (→ roundtrip unknown). Roundtrip: 2 yes, 7 no, 3 unknown.

## Checks
- `osm_id` unique.
