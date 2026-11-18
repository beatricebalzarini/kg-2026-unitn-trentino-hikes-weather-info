### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Lakes and glaciers of Trentino (including part of Lake Garda).


* **Data Structure**: 226 elements: 162 `way` (with `nodes` and `center`) and 64 `relation` (`type=multipolygon`, with `members` and `center`). There are no nodes and no full geometry: only `center` gives a position.


* **Members**: the 64 multipolygons have 380 `outer` and 94 `inner` (islands/holes) way members.


* **Types**: `natural=water` 159 (all with `water=lake`) and `natural=glacier` 67.


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`center`**: element kind, OSM id and a representative point.


* **`tags`**: present in every element, with `name` and `natural` always set (226 of 226).


### Optional Fields & Explanation

* **`water`**: `lake` (159), only for the `natural=water` elements.


* **`type`**: `multipolygon` (64), only on relations.


* **`ele`**: 47, plus `elevation` 3 (values like "2069 m.", a different format).


* **Names**: `alt_name` 20, `name:de` 15, `name:it` 14, `loc_name` 15, `old_name:de`, `name:en`, `name:lld` and, for Lake Garda, tens of other languages.


* **Links**: `wikidata` 108, `wikipedia` 28, `wikimedia_commons` 2, `ref:pat:id` and `ref:pat:cat` 7 (Provincia Autonoma di Trento references).


* **Uses**: `boat` 5, `fishing` 5, `swimming` 4, `motorboat` 2, `tourism` 3, `depth` 2, `wheelchair` 1.


* **Noisy tags**: `salt` 16, `tidal` 7, `intermittent` 10, `description` 9 ("Laghi naturali", "Ghiacciai perenni"), `source`, `fixme`, `area`, `image`.


# todo:
- remove timestamp
- divide by lake and glacier
- remove salt, tidal, wikidata, wikipedia

## suggested todo:
- split the file into `lakes` (`natural=water`) and `glaciers` (`natural=glacier`) as already planned: they behave very differently (swimming, fishing vs. high-altitude and ice)
- keep only the Italian/German/Ladin names, and drop the Lake Garda translations (`name:af`, `name:ar`, ...)
- normalize `ele` and `elevation` into a single numeric `ele` in metres
- fill missing `ele` (179 of 226) from a DEM, since altitude is useful for the weather
- find the lake area/perimeter from the polygon geometry (the file does not contain it, so re-export with `out geom` if needed)
- convert `swimming`, `fishing`, `boat`, `motorboat` into booleans, and remove `fixme`, `image`, `area`, `source*`
- link each lake to the nearest trails and huts, and to its municipality
