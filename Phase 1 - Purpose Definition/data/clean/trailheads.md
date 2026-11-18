# Cleaning: trailheads.json — NOT USED (no trailhead entity)

- **Source**: `data/trailheads.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Output**: none (user decision: option C)

## Input
3 `node` elements with `highway=trailhead`:

| Name | Nearest endpoint of a kept route |
|---|---|
| Salita al Maso di Agriconda | 1120 m ("Sentiero attrezzato dell'Angiom") |
| (no name) | 96 m ("Via Ferrata Marmolada Cresta Ovest") |
| punto di partenza del percorso dei mulini altolinor | 152 m (trail 531) |

None of them coincides with the endpoint of a kept route. 3 points are not enough to be useful.

## Options considered
A trailhead entity (`Trail startsAt Trailhead nearStop TransportStop`) would help CQ #11 (reachable by public transport), CQ #17 (trails near me) and the elderly/student personas.

The cleaned routes already carry `start` and `end` coordinates: 3514 endpoints, 3240 inside Trentino. Clustering them gives almost no reduction:

| Cluster radius | Trailheads | With only 1 route | With ≥ 5 routes |
|---|---|---|---|
| 20 m | 2648 | 2259 | 21 |
| 50 m | 2577 | 2147 | 27 |
| 100 m | 2498 | 2035 | 32 |
| 200 m | 2323 | 1782 | 47 |

This is because the SAT network in OSM is split into numbered stretches, and many trails end **where they join another trail** (e.g. "… (bivio 407)"), at a junction in the woods, not at a car park or a village. So most "trailheads" built from the endpoints would be trail junctions.

Options:
- **A**: one trailhead per cluster of endpoints (~2500 entities, mostly junctions).
- **B**: trailheads only where an endpoint is near a transport stop, a hut, a village centre or a car park (car parks are not in the data: new export needed).
- **C**: no trailhead entity; use the route `start`/`end` directly.

## Decision: option C
No trailhead entity is created in Phase 1, and `trailheads.json` is not used.
- No information is lost: every route keeps its `start` and `end` (`trails.json`, `mtb.json`, `foot_routes.json`, `via_ferrata.json`).
- The links "stop near the start of a route" (CQ #11) and "route near me" (CQ #17) will be computed from `start`/`end` in the spatial-join phase (Phase 4). Option B can still be built there if needed.
