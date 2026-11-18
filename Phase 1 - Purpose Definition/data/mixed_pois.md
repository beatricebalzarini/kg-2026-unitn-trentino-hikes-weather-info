### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Points of interest along trails in Trentino: signposts, information boards, drinking water, shrines, memorials, military remains, mines and caves.


* **Data Structure**: 17958 elements: 16525 `node` (with `lat`/`lon`), 1389 `way` (with `nodes` and `center`) and 44 `relation` (with `members` and `center`).


* **Main tags** (not exclusive): `tourism` 9062 (information 8723, attraction 298, artwork 16, museum 9, viewpoint 6), `historic` 5155, `amenity` 4076.


* **`tourism=information`** splits into `information=guidepost` 6395, `board` 1473, `map` 388, `route_marker` 216, `office` 102.


* **`amenity`**: `drinking_water` 3926, `place_of_worship` 75, `fountain` 24, `shelter` 9, `grave_yard` 7.


* **`historic`**: `wayside_shrine` 1532, `yes` 736, `wayside_cross` 660, `ruins` 547, `memorial` 484, `archaeological_site` 186, `mine` 160, `monument` 153, `castle` 105.


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id.


* **`tags`**: present in every element. At least one of `tourism`, `historic` or `amenity` is always set, but they can co-occur in the same element.


* **Location**: `lat`/`lon` for nodes, `center` for ways and relations.


### Optional Fields & Explanation

* **`name`**: only 3895 of 17958 (guideposts and drinking water usually have none). Some names repeat many times ("Calchera" 31, "Monumento ai caduti" 17).


* **Guideposts and boards**: `hiking` 3693, `support` 1137, `destination` 1082 (+ `direction_*` tags), `board_type` 901, `map_type`, `map_size`, `colour`, `mtb` 614, `bicycle`.


* **Religious**: `religion` 1440, `denomination` 819.


* **Water**: `fountain` 629 (drinking 568), `bottle` 134.


* **Military and mines**: `military` 367 (bunker 205, trench 150), `disused` 178, `resource` 124 (silver, fluorite, ...), `barrier` 228 (ditch, wall, ...).


* **Other**: `operator` 1080 (SAT 463 and "SAT" 105, Ecomuseo Argentario 91), `ele` 1012, `start_date` 333, `material` 487, `description` 334, `access` 394, `fee` 267, `wheelchair` 256, `memorial` 355, `wikidata` 796.


* **Noisy tags**: `check_date` 1231, `source` 296, `ref` 266 ("Sat", numbers, ...).


# todo:
- remove timestamp
- divide by amenity, tourism, historic
- remove check_date

## suggested todo:
- split the file by main category as already planned (`tourism`, `historic`, `amenity`) and, in addition, give each element exactly one `category` (the first rule that matches), so no element is counted twice
- split `tourism=information` further into guidepost / board / map / route_marker / office, because they are 8723 of the 17958 elements and carry different tags
- drop the most generic elements for a knowledge graph: guideposts without `name` and `destination` (they carry no information), or turn their `direction_*` and `destination` tags into links to the destination places
- separate drinking water (3926 points) as a distinct `water_point` class, keeping `fountain` and `bottle`
- normalize `operator` (SAT / Società degli Alpinisti Tridentini), `denomination` (catholic / roman_catholic), `military` (trench / trincea)
- convert `ele`, `start_date`, `fee`, `wheelchair` to proper numbers/dates/booleans; `start_date` mixes years and full dates
- turn ways and relations into points using `center`
- remove `source`, `ref`, `material`, `colour`, `map_size`, `map_type` and the `direction_*` tags if not used
- link each POI to the closest trail (trails.json, singular_paths.json) and municipality
