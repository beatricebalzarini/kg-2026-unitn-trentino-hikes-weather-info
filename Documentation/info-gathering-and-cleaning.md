# Information gathering and cleaning: from the raw OSM exports to the entity files

This document explains, step by step, how the data of the Trentino hikes KG went from the raw OpenStreetMap (OSM) exports to the files we have now. It is meant for the project team: after reading it you should know what each file is, why it looks the way it does, which decisions were taken and where to find the details.

Scope: Phase 1 (Purpose Definition, information gathering), OSM data only. The weather data is handled separately by another team member and is not covered here.

**Where things are** (all paths inside `Phase 1 - Purpose Definition/`):

| What | Where |
|---|---|
| Raw OSM exports (never modified) | `data/*.json` (+ one `.md` of metadata each) |
| Cleaning scripts | `cleaning/` |
| Intermediate cleaned files (one per source) + one `.md` per file | `data/clean/` |
| **Final entity files** (one per ER entity type) | `data/entities/` |
| Personas, scenarios, competency questions (CQs) | `initial-proposals.md` |
| ER model | `ER-model.md` |

---

## 1. The goal and the starting point

The purpose of the KG: help people choose a hike in Trentino (families with strollers, mountaineers, MTB riders, people in wheelchairs, ...). `initial-proposals.md` lists the personas and about 20 CQs, for example *which trails are stroller-friendly? have food points? are reachable by public transport? have a given height difference? pass by landmark X?*

The data comes from OpenStreetMap, downloaded with **Overpass Turbo** queries, one query per theme. The result is a set of JSON files, all with the same envelope (`version`, `generator`, `osm3s`, `elements`), where `elements` is a list of OSM objects:

- **node**: a point (`lat`, `lon`);
- **way**: a line, made of a list of node ids; it only has a `center` point unless the query asked for the full geometry;
- **relation**: a group of other objects with roles (for example a hiking route = the list of its ways).

Each object has a free-form `tags` dictionary (`name`, `surface`, `ele`, ...). An important detail: **an OSM id is unique only together with the object type** (`node/5` and `way/5` are different objects).

### The raw files (22)
| Theme | Files | Content |
|---|---|---|
| Routes | `trails`, `mtb`, `stroller`, `via_ferrata_routes` | route relations with full geometry (hiking 1657, bike 144, foot 13, via ferrata 29 relations + 235 ways) |
| Segments | `ways`, `full_stroller_mtb`, `singular_paths` | the ways (path segments), tags only, no geometry (26,507; 11,415; 11,954) |
| Points of interest | `huts_landmarks`, `mixed_pois`, `amenities` | huts, peaks, passes, viewpoints, signposts, fountains, shrines, restaurants, ... (5749; 17,958; 3145) |
| Lodging | `accomodations`, `hotels` | guest houses, camp sites, hostels (617) + hotels, apartments, motels (1765) |
| Water | `lakes`, `lakes_geom` | named lakes and glaciers: first with `center` only (226), then with polygons (227) |
| Transport | `public_transportation` | bus stops, stations, lifts (4948) |
| Administrative | `province_boundaries`, `municipalities` | the province (1) and its 166 municipalities |
| Other | `trailheads`, `parking` | 3 trailheads; 10,857 car parks |

Each raw file has an explanatory `.md` next to it (overview, structure, fields, a list of suggested todos). `hotels`, `lakes_geom` and `parking` were exported later, to fill gaps found during the cleaning (see section 5).

---

## 2. How we worked

1. **Decide what to keep before cleaning.** In `initial-proposals.md` we built a table *CQ → needed attribute → source file*. A field was kept only if it answers a CQ, or if it links two datasets (ids, coordinates, municipality code). Everything else (editing metadata, translations, urban/car tags, social links, ...) was dropped.
2. **Clean one source at a time.** For each file: analyse it, propose the changes with the reasons, get the team's approval, write the script, run it, write a `.md` documenting what was kept, removed and transformed.
3. **The raw files are never modified.** Cleaned data goes to new folders; each cleaning step is a script, so everything can be rebuilt.
4. **Everything is reproducible.** One command rebuilds all the outputs from the raw files (see section 9).

Principles applied everywhere:
- **A tag always wins**; values we compute or infer are marked in a `*_source` field (`surface_source`, `roundtrip_source`, `ele_source`, ...).
- **We never guess**: a value not stated by a tag stays `null`, meaning "not verified" (for example `food_service`).
- **Unnamed objects are not dropped**: they get a generated label `"{type} – {municipality}"` with `name_source = "generated"`.
- **Same real object = one entity**: duplicates are merged and the merged OSM ids are recorded.
- Things that may be useful later are parked in `_pending_*` files instead of being thrown away.

---

## 3. The cleaning steps, file by file

All the outputs below are in `data/clean/`; each has a `.md` with the full detail (kept/removed fields, rules, checks, results). Every script lives in `cleaning/`.

### 3.1 Spatial base: province and municipalities
- **`province_boundaries` → `province.json` + `province_boundary.geojson`.** The 170 boundary ways were merged into one valid polygon; the province became a flat entity (ISTAT code `022`, Trento as centre). This polygon is the **spatial filter** used by the other datasets.
- **`municipalities` → `municipalities.json` + `municipalities_boundaries.geojson`.** 166 municipalities, key = ISTAT code (6 digits). Names in other languages, population and cadastral codes were dropped. One municipality (Mori) has no centre node, so its centre is the polygon centroid (`centre_source` says so). Check: the union of the 166 polygons coincides with the province polygon.
- The **municipality of every point** (`municipality_istat`) is computed in all later steps with a point-in-polygon test on these boundaries.

### 3.2 Routes
Routes are OSM relations; the shared rules are in `route_common.py`.
- **Main line of a route**: the member ways with roles `""`, `forward`, `backward`, merged into one line. Variants, side trips and connections (`alternative`, `excursion`, ...) are excluded so they don't distort length and loop detection; **ways tagged as buildings are excluded** (a hut building that is a member of a trail would add its perimeter to the length).
- **Province filter**: a route is kept if **(1) it starts or ends in Trentino, or (2) at least 50% of its length is inside**. OSM has no reliable direction, so both endpoints are tested. The rule that kept each route is stored in `province_rule`.
- **Roundtrip**: the tag if present; otherwise, only if the ways merge into one line, `true` when start and end are within 50 m; otherwise `null` (not computed).
- **Numbers**: `distance` → km (float), `duration` "HH:MM" → minutes, `ascent`/`descent` → metres; a computed `length_km_computed` from the geometry is added next to the declared distance (87% of routes agree within ±10%).
- **Names**: the OSM name; if missing, `"{ref}: {from} – {to}"` and similar fallbacks (`name_source` says which).
- **Operators** are normalized (the many SAT/CAI/AVS spellings become one name).
- The geometry is saved apart in `*_geometry.geojson`; the JSON files only keep `start`/`end`.

| Source | Result | Specific decisions |
|---|---|---|
| `trails` | `trails.json`, 1585 | superroute and routes without geometry dropped; 70 routes outside Trentino dropped; `network`, symbols, sources, notes dropped; `wikidata` kept |
| `mtb` | `mtb.json`, 134 (85 mtb, 49 bicycle) | `state=proposed` routes dropped (not yet signposted); the 23 stages "SICAI Ciclo" get the stage in the name |
| `stroller` | `foot_routes.json`, 12 | **renamed**: nothing in the data says these routes are stroller-friendly (the filter existed only in the query: they contain steps, dirt paths, a main road). They are plain walking routes; stroller suitability is a derived attribute computed from segments |
| `via_ferrata_routes` | `via_ferrata.json`, 26 | the 29 relations have no members, 22 are already trails; the other via ferrata were **rebuilt by grouping ways by name**, keeping only groups proven equipped by the tags (`highway=via_ferrata`, `via_ferrata_scale`, `safety_rope`, a ferrata relation); unnamed ways, an escape route and routes outside Trentino dropped |

### 3.3 Segments (the ways)
Each route stores the ids of its ways (`main_way_ids`); the tags of the ways come from other files. All of `ways` (trails), `full_stroller_mtb` (bike and foot routes) and the via ferrata ways were merged into **one file, `ways.json`** (26,047 segments): the 2346 ways in both sources have identical tags (checked).
- Only the ways used by a kept route are kept; roads are kept too, because they tell how much of a route is paved.
- Fields: `highway`, `surface`, `smoothness` (1–8), `incline_pct`, `width_m`, `sac_scale`, `mtb_scale`, `bicycle_allowed`, `wheelchair`, `stroller`, `length_m` (computed from the geometry stored in the route files).
- **`surface_class` (paved / unpaved)**: from the tag; when `surface` is missing it is **inferred** from `highway` (primary → paved, path → unpaved, ...) or from `tracktype` for tracks, and `surface_source` marks it (`tag`, `inferred_highway`, `inferred_tracktype`). This is an assumption, not a measurement.
- Lifts used as stages of bike routes are kept with an `aerialway` field and no surface.
- `incline` is a number on only 1.6% of the segments ("up"/"down" carry no number): slope comes from the DEM (section 6).

### 3.4 Points of interest
Shared helpers are in `poi_common.py`. For points, ways and relations are turned into a point (`center`); positions are `lat`/`lon`.

| Source | Result | Specific decisions |
|---|---|---|
| `huts_landmarks` | `huts.json` (745), `landmarks.json` (4386) | every element gets **one category** (`alpine_hut`, `wilderness_hut`, `emergency_shelter`; `peak`, `saddle`, `viewpoint`, `waterfall`, `cave_entrance`, `cliff`). Shelters are split by `shelter_type`: bus shelters and picnic shelters are parked in `_pending_*` files; untyped shelters without name dropped. `food_service` is `true` only if a tag says so (`cuisine` or a food `amenity`), else `null`. Unnamed landmarks are kept with generated names |
| `mixed_pois` | `water_points` (3950), `cultural_landmarks` (4910), `guideposts` (1352), `tourist_info` (105), `rest_areas` (268) | split by type with one category each. Guideposts: kept only if named or on a kept route (5037 anonymous ones dropped); information boards, maps and route markers dropped; unnamed `historic=yes` dropped; unnamed shrines and crosses kept with a generated name |
| `amenities` | `food_drink.json` | restaurants, bars, cafes, fast food, pubs; kept `cuisine`, `outdoor_seating`, `takeaway`, `diet_*`, `wheelchair` |
| `accomodations` + `hotels` | `accommodations.json` | one file for all accommodation types; `stars` as an integer ("3S" → 3); same name + same category + within 200 m → merged (a structure mapped twice, or the units of a holiday village); the structures on Lake Garda are kept |
| `lakes_geom` | `lakes.json` (160), `glaciers.json` (67) + polygon files | rule: **any part of the polygon inside Trentino**; `area_km2`, `area_inside_pct`, list of the Trentino municipalities touched; a point guaranteed inside the polygon. Lakes with the same name are different objects and are renamed ("Lago Nero (Pinzolo)", "Tre Laghi – basin 1"), the original name stays in `name_osm` |
| `public_transportation` | `transport_stops` (3781), `aerialways` (204) | stops with the same name, mode and within 100 m merged; the 203 bus shelters parked earlier are matched to the nearest stop within 30 m (`has_shelter`); operators normalized; lift seats and capacity dropped |

Not used: `singular_paths` (its useful ways are already in `ways.json`, the other 6930 belong to no route), `trailheads` (3 points, none at a route end: we use route `start`/`end`; trailheads may be built in Phase 4), `parking` (exported but not cleaned: only needed if trailheads are built), the first `lakes.json` export (replaced by `lakes_geom`).

---

## 4. Cleaning across files

After each file was cleaned on its own, three problems appeared that no single file could solve.

1. **Same OSM object in two sources.** Several scripts exclude objects already cleaned elsewhere (e.g. the 48 huts with a restaurant are in both `huts_landmarks` and `amenities`: kept only as huts; the same for 93 hotels/guest houses with a restaurant).
2. **Same real object, different OSM ids** (a hotel and its restaurant as two points, a hut mapped as a building and as a point, a waterfall also tagged as an attraction). `dedup_cross_files.py` merges them with the rule *same name + within 100 m + compatible pair of files*; 50 duplicates were removed. It runs last because it rewrites several files. `cross_file_duplicates.md` lists them.
3. **One OSM object with two roles** (a lift that is also a route segment, trenches that are also trail segments): it keeps the same id in both files and becomes one entity with two types in the KG (13 cases, `_shared_objects.json`).

**Uniform ids.** Every id is `"{type}/{id}"` (`relation/129319`, `way/4699598`, `node/123`), ISTAT code for municipalities and province, `via_ferrata/<slug>` for the rebuilt via ferrata. In the KG the id becomes the entity URI.

---

## 5. Extra exports and open issues
Three things were not possible with the first exports and needed new Overpass queries (documented in `data/hotels.md`, `data/lakes_geom.md`, `data/parking.md`):
- **Hotels were missing**: the first accommodation query had no `tourism=hotel|apartment|motel` → `hotels.json`, merged into `accommodations.json`.
- **Lakes had no polygons**, so large lakes (Garda) and border glaciers could not be filtered by province → `lakes_geom.json`.
- **Car parks** (optional): exported, not cleaned.

Remaining and decided points are in `data/clean/OPEN_ISSUES.md` (weather handled separately; no trailhead entity; car parks on hold; ...).

---

## 6. Missing elevations: the DEM
OSM geometries have no elevation: only some objects have an `ele` tag. CQs on height difference, slope and maximum altitude need it everywhere, so we added a **DEM** (a grid of elevations): Copernicus DEM GLO-30 (30 m), 6 tiles of 251 MB in total, downloaded by `fetch_dem.py` into `data/dem/` (git-ignored; attribution required, see `data/entities/dem.md`).

`enrich_dem.py` **only fills null fields** (the tag always wins) and marks them `dem`:
- **points**: elevation under the point; **lakes and glaciers**: median elevation inside the polygon;
- **routes**: the line is resampled every 30 m; `ele_from/to/max/min`; **ascent/descent** = sum of the changes above a 15 m threshold (calibrated on 542 routes with both OSM values: total climb ratio DEM/OSM 1.01); **`max_incline_pct`** = 95th percentile of the slope over 100 m windows on a smoothed profile (the plain maximum is dominated by artefacts on bridges and steep side slopes).

Validation against the OSM `ele` tags (`dem_validation.json`): median difference of a few metres for huts, saddles, guideposts and lakes (about 90% within 25 m). Known limits: peaks come out about 20 m too low (30 m cells flatten the summit: peaks keep their tag), and the DEM ascent is measured from `start` to `end` of the geometry, which for about half of the routes is the opposite of OSM's `from` → `to`.

The ER model did not change: only existing empty fields were filled, plus `Route.max_incline_pct` (already in the ER) and provenance fields. Result: every route and point has an elevation.

---

## 7. From the sources to the ER model
With the ER model of `ER-model.md` (8 entity types) fixed, the cleaned files were regrouped into **one file per entity type** by `build_entities.py`:

| Entity file | Entities | Built from (`data/clean/`) |
|---|---|---|
| `routes.json` (+ `routes_geometry.geojson`) | 1757 | trails, mtb, foot_routes, via_ferrata |
| `segments.json` | 26,047 | ways |
| `landmarks.json` (+ `landmarks_geometry.geojson`) | 9523 | landmarks, lakes, glaciers, cultural_landmarks |
| `hospitality.json` | 5698 | huts (alpine, wilderness), accommodations, food_drink |
| `facilities.json` | 6026 | water_points, rest_areas, guideposts, tourist_info, huts (emergency shelters) |
| `transport.json` | 3985 | transport_stops, aerialways |
| `municipalities.json` (+ boundaries) | 166 | municipalities |
| `province.json` (+ boundary) | 1 | province |
| **total** | **53,203** | |

Modelling choices behind the grouping: lakes and glaciers are Landmarks (reached or seen along a route); fountains, rest areas, signposts and tourist offices are Facilities (otherwise "at least 3 landmarks" would be flooded by 4000 fountains); huts, accommodation and food & drink places are one Hospitality entity with two attributes, `overnight` and `food_service` (CQ #5 and #4); stops and lift lines are one Transport entity; Municipality and Province stay separate to keep the `partOf` relationship.

**Uniform schema.** In every entity file all rows have the same fields in the same order: `id`, `name`, `name_source`, `name_osm`, `category` first; position, municipality, `wikidata`, `source_dataset` (the raw export), `merged_osm_ids` and provenance fields last. The subtype of an entity is always `category`. The `name_source` vocabulary is common (`name`, `name_stage`, `name_disambiguated`, `ref_from_to`, `ref`, `from_to`, `generated`). `data/entities/SCHEMA.md` is **generated from the data** and documents every field (type, fill rate, values, meaning) and the references between files.

Shared rules (distances, operator normalization) are in `normalize.py`, one place for each rule.

---

## 8. What is not done yet (next steps)
- **Derived Route attributes**: `paved_pct`, `stroller_suitable`, `wheelchair_suitable`, from the segments (rules to be agreed, e.g. no steps, paved or compact surface, low SAC scale).
- **Relationships** that need spatial joins: `passesBy`, `nearTo`, `startsNear`, `crosses`, `hasStation`, with the distances to be fixed.
- **Weather** (separate): to be linked to routes with a weather cell and an elevation band; the "elevation of the route" is now available.
- **Metadata** for the catalogue in `Metadata/` (from the `.md` files described here).
- **Review of the `null` values**: too many fields of the entity files are mostly empty (the *Filled* column of `data/entities/SCHEMA.md` shows how much). Planned work: decide which fields are really needed (by the CQs and the ER model); **drop the sparse fields that are not needed**; for the sparse fields that are needed, decide how to handle them (derive them from other data, fill them from another source, or accept partial answers and document the limit). Also tracked as issue #10 in `data/clean/OPEN_ISSUES.md`.

---

## 9. How to rebuild everything
From the repository root (needs `shapely`, `pyproj`, `rasterio`, installed in `.venv`; the first run downloads the DEM, about 250 MB):

```
.venv/bin/python "Phase 1 - Purpose Definition/cleaning/run_all.py"
```

It runs 18 steps in order (several scripts read the outputs of the previous ones), then runs integrity checks: ids unique and in the uniform format, every `segment_id` of a route exists, every municipality code exists, the province lists exactly the 166 municipalities. It writes a hash of every output in `cleaning/last_run_hashes.json`: **two consecutive runs give identical files**.

| # | Step | Produces |
|---|---|---|
| 1–2 | `clean_province_boundaries`, `clean_municipalities` | province, municipalities |
| 3–6 | `clean_trails`, `clean_mtb`, `clean_stroller`, `clean_via_ferrata` | routes |
| 7 | `clean_ways` | segments |
| 8–13 | `clean_huts_landmarks`, `clean_accommodations`, `clean_amenities`, `clean_lakes`, `clean_mixed_pois`, `clean_public_transport` | points of interest and transport |
| 14 | `dedup_cross_files` | removes the duplicates between files |
| 15 | `build_entities` | `data/entities/` (one file per ER entity) |
| 16–17 | `fetch_dem`, `enrich_dem` | missing elevations, ascent, slope |
| 18 | `schema_report` | `data/entities/SCHEMA.md` |

**Important**: always rebuild with `run_all.py`. Running a single script alone can leave the files inconsistent (for example `clean_mixed_pois.py` rewrites files that `dedup_cross_files.py` then corrects).

## 10. Where to read more
| For | Read |
|---|---|
| Every cleaned file: kept/removed fields, rules, checks | `data/clean/<name>.md`, `data/clean/README.md` |
| Duplicates between files | `data/clean/cross_file_duplicates.md` |
| Decisions still open | `data/clean/OPEN_ISSUES.md` |
| Fields of the final files | `data/entities/SCHEMA.md`, `data/entities/README.md` |
| Elevation enrichment | `data/entities/dem.md` |
| ER model, CQ coverage | `ER-model.md`, `initial-proposals.md` |
| Raw exports | `data/<name>.md` |
