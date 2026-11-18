### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data. OSM data timestamp: 2026-11-18T12:00:28Z. Data © OpenStreetMap contributors, ODbL.


* **Query** (Overpass Turbo):
  ```
  [out:json][timeout:300];
  area(id:3600045756)->.tn;
  (
    way["natural"="water"]["water"="lake"]["name"](area.tn);
    relation["natural"="water"]["water"="lake"]["name"](area.tn);
    way["natural"="glacier"]["name"](area.tn);
    relation["natural"="glacier"]["name"](area.tn);
  );
  out geom;
  ```
  Same selection as `lakes.json`, but with **full geometry** (`out geom`). It replaces `lakes.json`, which had only a `center` (see `clean/OPEN_ISSUES.md` #2).


* **Geographical Scope**: Named lakes and glaciers that touch the Autonomous Province of Trento (area of relation 45756). The area filter keeps the ways/relations with at least a part in the area, so it includes large border objects such as Lake Garda, Lake Idro and the glaciers shared with Lombardia and Alto Adige.


* **Data Structure**: 227 elements: 163 `way` (with `bounds`, `nodes` and a closed `geometry` ring of `lat`/`lon` points, 8002 points in total) and 64 `relation` (`type=multipolygon`, with `bounds` and `members` whose ways carry `geometry`: 380 `outer` and 94 `inner` rings, 27,861 points in total). No `center`. The largest geometries: Lago di Garda (10,534 points), Ghiacciaio dei Forni (1838), Lago d'Idro (1477), Ghiacciaio della Marmolada (953).


* **Types**: `natural=water` 160 (all with `water=lake`) and `natural=glacier` 67.


* **Difference with `lakes.json`**: same 226 elements (same OSM ids) plus 1 new: "Laghi dei Lasteati" (way 103589637), added in OSM after the first export.


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`bounds`**: element kind, OSM id and bounding box.


* **Geometry**: `geometry` (closed ring) for ways; `members` with `role` (`outer`/`inner`) and `geometry` for relations. All 227 geometries can be built into valid polygons (outer rings minus inner rings).


* **`tags`**: present in every element, with `name` and `natural` always set.


### Optional Fields & Explanation
Same tags as `lakes.json`:

* **`water`**: `lake` (160), only for `natural=water`.
* **`ele`**: 47, plus `elevation` 3 (values like "2069 m.").
* **Names**: `alt_name` 20, `name:de` 15, `name:it` 14, `loc_name` 15, `old_name:de`, `name:en`, `name:lld`, and many translations for Lake Garda.
* **Links**: `wikidata` 108, `wikipedia` 28, `wikimedia_commons` 2, `ref:pat:id` / `ref:pat:cat` 7.
* **Uses**: `boat` 5, `fishing` 5, `swimming` 4, `motorboat` 2, `tourism` 3, `depth` 2, `wheelchair` 1.
* **Noisy tags**: `salt` 16, `tidal` 7, `intermittent` 10, `description` 9, `source`, `fixme`, `area`, `image`.


### Border objects: share of the area inside Trentino
The 14 elements whose centre was outside Trentino in `lakes.json`, measured with the polygons of this file:

| Name | Area inside Trentino |
|---|---|
| Vedretta del Mandrone | 15% |
| Vedretta del Rosole | 6% |
| Lago di Garda | 4% |
| Fürkeleferner - Vedretta della Forcola | 1% |
| Ghiacciaio dei Forni | 1% |
| Lago d'Idro, Ultenmarktferner - Vedretta Ultima, Vedretta del Pasquale, Ghiacciaio di Dosegù, Ghiacciaio dell'Adamello, Gramsenferner - Vedretta di Grames, Hohenferner - Vedretta Alta, Zufallferner - Vedretta del Cevedale, Vedretta di Pisgana | < 1% (they only touch the border) |


# todo (suggested):
- remove timestamp
- clean it with the same rules as `lakes.json` (`cleaning/clean_lakes.py`): split lakes / glaciers, same fields, same renaming of same-name objects; this file then replaces `lakes.json` as the source
- decide the province rule for the border objects now that the polygons are available (e.g. keep if any part is inside, or if at least X% of the area is inside): with a 50% rule all 14 would be dropped, including Lake Garda (4%); with "any part inside" they are all kept
- compute `area_km2` and keep a simplified polygon (or the shore line) in a separate GeoJSON, as for the routes: it allows "trail passes by lake X" (CQ #21) to use the distance from the shore instead of from the centre
- compute a representative point inside the polygon (the old `center` can fall outside the lake for irregular shapes) and the municipality from it
- remove `salt`, `tidal`, `wikipedia`, the Lake Garda translations, `fixme`, `image`, `area`, `source*`
