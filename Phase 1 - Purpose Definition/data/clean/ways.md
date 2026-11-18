# Cleaning: ways.json + full_stroller_mtb.json + via ferrata ways → ways.json (all route segments)

- **Sources** (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL):
  - `data/ways.json`: segments of the hiking trails (`trails.json`)
  - `data/full_stroller_mtb.json`: segments of the bike routes (`mtb.json`) and foot routes (`stroller.json`)
  - `data/via_ferrata_routes.json`: the ways of the via ferrata rebuilt in `via_ferrata.json` (see `via_ferrata.md`)
- **Script**: `cleaning/clean_ways.py`
- **Other inputs**: the raw route files `data/trails.json`, `data/mtb.json`, `data/stroller.json`, `data/via_ferrata_routes.json` (for the way geometry), and the cleaned `data/clean/trails.json`, `mtb.json`, `foot_routes.json`, `via_ferrata.json` (for `main_way_ids`)
- **Output**: `data/clean/ways.json`: **26,047 way segments** of all the kept routes (one file, user decision)

## Input
| Source | Ways | Content |
|---|---|---|
| `ways.json` | 26,507 | tags only (no geometry). Exactly the way members of `trails.json` (100% match on the ids) |
| `full_stroller_mtb.json` | 11,415 | tags only (no geometry). Exactly the way members of `mtb.json` + `stroller.json` (100% match). Includes 19 aerialways (lifts) |
| `via_ferrata_routes.json` | 235 ways (+ 29 relations) | ways with their own geometry. 149 are already segments of kept trails; 49 are the segments of the 26 via ferrata in `via_ferrata.json` |

Main tags: `highway`, `surface`, `sac_scale`, `tracktype`, `mtb:scale`, `width`, `smoothness`, `incline`, `wheelchair`, `stroller`, plus about 150 traffic/urban/editing tags.

## Role in the KG
Each way is a **segment** of one or more routes of any kind (`trail.main_way_ids`, `mtb.main_way_ids`, `foot_route.main_way_ids`, `via_ferrata.main_way_ids` → `way.osm_id`). The route-level properties needed by the CQs (% paved, max incline, stroller/wheelchair suitability, bike suitability) will be computed in the integration step by aggregating these segments weighted by `length_m`, with the same rule for every route kind.

## Why one file
- 2346 ways are in both sources, and 1813 of them are used both by a kept trail and by a kept bike/foot route.
- **Their tags are identical in the two sources** (0 differences, checked by an assertion in the script), so merging creates no conflict.
- With one file every route joins the same segments, and the stroller/wheelchair rule is applied once.

## Filtering
| Rule | Dropped | Why |
|---|---|---|
| Way of `ways.json` not among the `main_way_ids` of a kept trail | 6304 | segments of trails dropped by the province filter, or of alternative/excursion branches |
| Way of `full_stroller_mtb.json` not among the `main_way_ids` of a kept bike/foot route | 3804 | segments of routes dropped (province filter, `state=proposed`, ...) |
| Way of `full_stroller_mtb.json` already taken from `ways.json` | 1813 (not dropped: merged) | same OSM way, identical tags |
| Element of `via_ferrata_routes.json` not among the `main_way_ids` of a kept via ferrata | 215 | the 29 relations, the 149 ways already segments of kept trails (already in the output from `ways.json`), and the unnamed/not kept ways (see `via_ferrata.md`) |

Ways tagged `building` (3: the buildings of Rifugio Boé, Rifugio Pisciadù and Santuario della Madonna di Làghel) are not route segments: the route scripts exclude them from `main_way_ids`, so they are not here.

Kept: 20,201 from `ways.json` + 5797 from `full_stroller_mtb.json` + 49 from `via_ferrata_routes.json` = **26,047**.

Road ways (`residential`, `tertiary`, `secondary`, `primary`, `unclassified`, `service`) and cycleways are **kept**, unlike what the original `ways.md`/`full_stroller_mtb.md` suggested: they are real stretches of the routes, and they are what tells us how much of a route is paved.

## Output fields
| Field | Source / transformation | CQ |
|---|---|---|
| `osm_id` | `"way/{id}"` (uniform id format `{type}/{id}`, see `README.md`) | key, join with `main_way_ids` |
| `highway` | as is (path, track, residential, cycleway, steps, via_ferrata, ...); `null` for lifts | segment type (e.g. `steps` excludes strollers) |
| `aerialway` | `gondola` / `chair_lift` / `cable_car` for the 13 lifts used as stages of bike routes, else `null` | to exclude lifts from surface/slope aggregates; later link with `public_transportation` |
| `length_m` | geodesic (haversine) length of the way geometry taken from the raw route files | weight for route-level percentages |
| `surface` | `surface`, with non-standard values mapped to OSM ones (see below) | #16 (asphalt) |
| `surface_class` | `paved` / `unpaved` / `null` (see below) | #3, #7, #15, #16 |
| `surface_source` | `tag`, `inferred_highway`, `inferred_tracktype` or `null` | provenance |
| `smoothness` | ordinal: excellent 1, good 2, intermediate/medium 3, bad 4, very_bad 5, horrible 6, very_horrible 7, impassable 8 | #3, #15 |
| `incline_pct` | absolute slope in % (see below) | #2 |
| `width_m` | float metres (see below) | #3, #15 |
| `sac_scale` | ordinal: strolling 0, hiking 1, mountain_hiking 2, demanding_mountain_hiking 3, alpine_hiking 4, demanding_alpine_hiking 5, difficult_alpine_hiking 6; multi-valued → max | difficulty |
| `mtb_scale` | 0–6, `+`/`-` removed, multi-valued (`0;1`, `2;1`) → max | #10 |
| `bicycle_allowed` | `yes`/`designated`/`permissive`/`mtb`/`official` → true; `no`/`dismount`/`private` → false; otherwise (`unknown`, missing) null | #10 |
| `wheelchair` | as is: `yes`/`limited`/`no` | #15 |
| `stroller` | as is: `yes`/`no` | #3 |
| `via_ferrata_scale` | as is (0 … 4, with `+`/`-`) | #19 |

## Transformations

### Surface
1. **Normalization of the values**: `sterrato` → `unpaved`, `selciato` → `sett`, `cement` → `concrete`, `rocky` → `rock`, `unpaved,_cement` → `unpaved`, `gravel;ground` → `gravel`, `dirt;sand` → `dirt`, `metal grid` → `metal_grid`, `rubber` → `paved`.
2. **Class from the tag**:
   - `paved`: asphalt, chipseal, concrete (and :plates, :lanes), paved, paving_stones, sett, cobblestone (and variants), unhewn_cobblestone, stone, grass_paver, metal, metal_grid, wood
   - `unpaved`: unpaved, ground, earth, dirt, mud, gravel, fine_gravel, compacted, pebblestone, grass, rock, bare_rock, sand, woodchips, ice, snow
   - `mixed` (2 ways): no class
3. **Inference when `surface` is missing** (user decision), marked in `surface_source`:
   - `inferred_highway` → `paved`: primary(_link), secondary(_link), tertiary, trunk_link, unclassified, residential, living_street, service, pedestrian, footway, cycleway
   - `inferred_highway` → `unpaved`: path, via_ferrata, bridleway
   - `inferred_tracktype` (only `highway=track`): `tracktype=grade1` → `paved`, `grade2`–`grade5` or no tracktype → `unpaved`
   - `steps`, `construction`, `road`, missing `highway`, lifts: no class (`null`)
   - `surface` itself stays `null` when inferred: only the class is inferred, so CQ #16 ("totally asphalted") can rely on real `asphalt` tags only.

**This is an assumption, not a measured value**: e.g. some `unclassified` or `service` roads in the mountains may be unpaved.

### Other numbers
- **`incline_pct`**: only numeric values are used, as absolute values (the sign only depends on the direction of the way): `"20%"`, `"-15%"`, `"10"`, `"+12"` → 20, 15, 10, 12. `"30°"` converted with tan → 57.7%. `up`, `down`, `up/down`, `steep`, `yes` carry no number → `null`.
- **`width_m`**: decimal comma and units removed (`"0.5 m"`, `"6 m"`, `".3"`). Values above 20 (`60`, `75`, `54`) are read as centimetres and divided by 100. `0` → `null`.

### Lifts
13 aerialways (8 gondolas, 4 chair lifts, 1 cable car, e.g. "Col Rodella", "Funifor Arabba - Portavescovo", "Dantercëpies I/II") are members of kept bike routes (lift-assisted tours in the Dolomites). They are kept as segments with `aerialway` set and no surface, so they can be excluded from surface/slope aggregates. The 6 lifts of `full_stroller_mtb.json` not used by a kept route are dropped.

## Removed
| What | Why |
|---|---|
| `tracktype` | used only to infer `surface_class` for tracks without `surface` (user decision), then dropped: the CQs use `surface_class` and `smoothness` |
| `trail_visibility` | not used by any CQ (user decision) |
| `name`, `name:*`, `alt_name`, `ref`, `old_ref`, `nat_ref`, `loc_ref`, `ref:*`, `sac_scale_ref`, `*:etymology*` | segment names/numbers: the route carries the label |
| `foot`, `horse`, `motor_vehicle`, `motorcar`, `motorcycle`, `vehicle`, `hgv`, `access`, `emergency`, `forestry`, `designation`, `disabled` | access for other users, not used by any CQ |
| `lit`, `lanes`, `lane_markings`, `maxspeed*`, `maxweight`, `oneway`, `cycleway*`, `sidewalk*`, `segregated`, `crossing`, `junction`, `parking:*`, `layer`, `bridge`, `tunnel`, `tactile_paving`, `inline_skates`, `ramp`, `handrail`, `step_count`, `dog` | road/urban details |
| `mtb:scale:uphill`, `mtb`, `hiking`, `class:bicycle`, `safety_rope` | rare or redundant with the kept fields |
| `aerialway:capacity`, `aerialway:duration`, `aerialway:occupancy` | lift details: they belong to the public transport dataset |
| `piste:*` | winter ski slopes |
| `source*`, `fixme`, `note*`, `description`, `check_date*` | editing metadata |

## Results
- 26,047 segments (13 lifts).
- Surface class weighted by length (lifts excluded): unpaved 76.1% (tag 34.6%, inferred from highway 30.3%, inferred from tracktype 11.2%), paved 23.8% (tag 19.9%, highway 3.3%, tracktype 0.6%), unknown 0.1%.
- By count: `surface_source` tag 16,297, inferred_highway 6888, inferred_tracktype 2783, null 79.
- Filled values: `sac_scale` 7007, `bicycle_allowed` 6055, `mtb_scale` 4091, `smoothness` 2269, `width_m` 2085, `incline_pct` **413**, `wheelchair` 315, `stroller` 44.

## Checks (all passed)
- Every `main_way_id` of the kept trails, bike routes, foot routes and via ferrata exists in the output.
- Ways present in both sources have identical tags.
- Every kept way has a `length_m`.

## Open points
- **`incline_pct` is available on only 413 ways (1.6%)**, so CQ #2 (max slope) and the MTB persona (slope ≤ 15%) cannot be answered from OSM tags alone. Options: a DEM to compute slopes from the geometry, or answering only partially.
- `wheelchair` (315) and `stroller` (44) are rare: CQ #3 and #15 will need a rule based on `surface_class`, `smoothness`, `width_m`, `highway` (no `steps`) and `sac_scale`.
