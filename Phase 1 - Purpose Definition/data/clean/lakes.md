# Cleaning: lakes_geom.json → lakes.json + glaciers.json

- **Source**: `data/lakes_geom.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL), second export **with full polygons** (see `data/lakes_geom.md`). It replaces `data/lakes.json` (first export, `center` only), which is **no longer used**.
- **Script**: `cleaning/clean_lakes.py` (shared POI helpers in `cleaning/poi_common.py`; `pyproj` for geodesic areas)
- **Other inputs**: `data/clean/municipalities_boundaries.geojson`, `data/clean/municipalities.json`
- **Outputs** (split by type, as in the original todo):
  - `data/clean/lakes.json`: **160** lakes (`natural=water`, `water=lake`), 394.0 km² in total
  - `data/clean/glaciers.json`: **67** glaciers (`natural=glacier`), 57.8 km² in total
  - `data/clean/lakes_geometry.geojson`, `data/clean/glaciers_geometry.geojson`: the polygons (not simplified), for the spatial joins (e.g. distance from the shore for CQ #21)

## Input
227 elements: 163 `way` (closed ring in `geometry`) and 64 `relation` (`type=multipolygon`, 380 `outer` and 94 `inner` rings with `geometry`). Every element has a `name`. Same 226 elements as `lakes.json` plus "Laghi dei Lasteati" (way 103589637), added in OSM after the first export.

## Geometry
- Ways: the ring is the polygon. Relations: `outer` rings merged and polygonized, `inner` rings (islands) subtracted. All 227 polygons are valid.
- `area_km2`: geodesic area on the WGS84 ellipsoid.
- Position (`lat`, `lon`): a **point guaranteed inside the polygon, taken in its Trentino part** (`representative_point` of polygon ∩ province). For border objects such as Lake Garda, the point is in the Trentino part of the lake (near Riva), not in Lombardia/Veneto. All the points are inside Trentino (checked).

## Filtering: province rule (a) (user decision)
An element is kept if **any part of its polygon is inside Trentino**. All 227 elements touch the province (the Overpass area filter already selected them this way), so none is dropped.

The share inside Trentino is stored in `area_inside_pct`, so a query can filter if needed. Elements partly outside:

| Type | Name | Area inside Trentino |
|---|---|---|
| lake | Lago d'Idro | 0.3% |
| lake | Lago di Garda | 3.9% |
| lake | Lago degli Zingari | 96.2% |
| glacier | Ghiacciaio dell'Adamello, Hohenferner - Vedretta Alta, Vedretta di Pisgana | 0.0% (they only touch the border line) |
| glacier | Gramsenferner - Vedretta di Grames, Ultenmarktferner - Vedretta Ultima, Vedretta del Pasquale, Zufallferner - Vedretta del Cevedale, Ghiacciaio di Dosegù | 0.1–0.3% |
| glacier | Ghiacciaio dei Forni, Fürkeleferner - Vedretta della Forcola | 1.0–1.5% |
| glacier | Vedretta del Rosole | 6.3% |
| glacier | Vedretta del Mandrone | 14.7% |
| glacier | Vedretta del Orsi, Vedretta de la Mare, Vedretta Rossa, Ghiacciaio della Marmolada | 92.6–99.2% |

## Municipalities
`municipalities_istat` is the **list of the Trentino municipalities** touched by the polygon (user decision), sorted by overlap (largest first). Municipalities outside Trentino are not listed. Examples: Lago di Garda → Riva del Garda, Nago-Torbole, Arco, Ledro; Lago di Caldonazzo → 5 municipalities; Lago d'Idro → Bondone. 7 lakes and 11 glaciers touch more than one municipality.

## Same names: kept as different objects, renamed
Several elements share a name. They are **different objects** and are **not merged** (user decision). To make every name unique, they are renamed; the original OSM name stays in `name_osm`:

- **closer than 1 km** (basins or parts of the same water body / glacier): `"{name} – basin N"` for lakes, `"{name} – part N"` for glaciers, numbered north → south (`name_source = osm_basin` / `osm_part`);
- **farther apart** (different lakes): `"{name} ({municipality})"`, with the municipality of largest overlap (`name_source = osm_municipality`).

| OSM name | Elements | Max distance | New names |
|---|---|---|---|
| Laghetto del Vedes | 2 | 43 m | Laghetto del Vedes – basin 1 / 2 |
| Tre Laghi | 3 | 239 m | Tre Laghi – basin 1 / 2 / 3 |
| Ghiacciaio di Cornisello | 2 | 362 m | Ghiacciaio di Cornisello – part 1 / 2 |
| Lago di Terlago | 2 (way + relation) | 719 m | Lago di Terlago – basin 1 / 2 |
| Lago Grande | 2 | 12 km | Lago Grande (Bieno), Lago Grande (Ronchi Valsugana) |
| Lago Santo | 2 | 14 km | Lago Santo (Cembra Lisignago), Lago Santo (Vallelaghi) |
| Lago Scuro | 2 | 18 km | Lago Scuro (Pinzolo), Lago Scuro (Spiazzo) |
| Lago Nero | 4 | 89 km | Lago Nero (Carisolo), (Pinzolo), (Valdaone), (Ziano di Fiemme) |

All the other elements keep their OSM name (`name_source = osm`). Names are unique in each file (checked).

## Output fields
| Field | Source / transformation | Applies to | CQ |
|---|---|---|---|
| `osm_id` | `"{type}/{id}"` | both | key |
| `name` | `name`, disambiguated when shared (see above) | both | label, #21 |
| `name_osm` | the original OSM `name` | both | provenance |
| `name_source` | `osm`, `osm_basin`, `osm_part`, `osm_municipality` | both | provenance |
| `ele_m` | `ele`, else `elevation` (`"2069 m."` → 2069) → integer | both (lakes 50, glaciers 0) | #9 |
| `ele_source` | `ele`, `elevation` or `null` | both | provenance |
| `area_km2` | geodesic area of the polygon | both | – |
| `area_inside_pct` | % of the area inside Trentino | both | province rule |
| `lat`, `lon` | point inside the Trentino part of the polygon | both | spatial joins |
| `municipalities_istat` | list of the Trentino municipalities touched, largest overlap first | both | #22 |
| `wikidata` | as is (lakes 99, glaciers 9) | both | linking |
| `swimming` | `yes`/`no` → boolean (4) | lakes | – |
| `fishing` | **kept as a value**: `yes` / `no` / `license` (allowed only with a fishing licence), not forced to a boolean (5) | lakes | – |
| `boat` | `yes`/`no` → boolean (5) | lakes | – |

## Removed
| What | Why |
|---|---|
| `natural`, `water` | used for the split (`water` is always `lake`) |
| `type` (`multipolygon`), `bounds`, `nodes`, `members` | OSM structure (the geometry goes to the GeoJSON files) |
| `salt`, `tidal`, `intermittent`, `depth`, `area` | not used by any CQ (salt/tidal in the original todo) |
| `motorboat`, `tourism`, `wheelchair`, `website` | 1–3 occurrences, not used by any CQ |
| `description` ("Laghi naturali", "Ghiacciai perenni", ...) | generic text |
| `name:*`, `alt_name`, `loc_name`, `old_name:*`, `reg_name` (incl. the tens of Lake Garda translations) | name variants |
| `wikipedia`, `wikimedia_commons`, `image`, `source*`, `fixme`, `ref:pat:id`, `ref:pat:cat` | links, editing metadata, official refs (`wikidata` kept) |

## Checks (all passed)
- All polygons valid; `osm_id` and `name` unique in each output.
- Every element touches at least one Trentino municipality; every point is inside Trentino.

## Open points
- `ele_m` is missing for 110 lakes and all 67 glaciers: DEM enrichment, planned after the integration.

## Final count
After the cross-file step (`dedup_cross_files.py`, see `cross_file_duplicates.md`): Lago di Caldonazzo and Lago di Levico absorb their duplicate in `cultural_landmarks.json` (`duplicates`). Counts unchanged.
