### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Mountain huts, shelters and natural/cultural landmarks of Trentino.


* **Data Structure**: 5749 elements: 4674 `node` (with `lat`/`lon`), 1073 `way` (with `nodes` and `center`) and 2 `relation` (with `members` and `center`).


* **Categories** (which tag defines them): `natural` 3252 (peak 1982, saddle 723, cave_entrance 537, cliff 10), `tourism` 1352 (viewpoint 939, alpine_hut 235, wilderness_hut 161, attraction 9, information 6, picnic_site 2), `amenity` 1043 (shelter 971, restaurant 47, bench 19, ...), `waterway=waterfall` 244, `historic` 136 (bunker 80, ruins 25, ...), `man_made` 111.


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id.


* **`tags`**: present in every element. No single tag is guaranteed: each element has at least one of `natural`, `tourism`, `amenity`, `waterway`, `historic` or `man_made`.


* **Location**: `lat`/`lon` for nodes, `center` for ways and relations.


### Optional Fields & Explanation

* **`name`**: 3567 of 5749 (many caves and shelters are unnamed). `name:it` 119, `name:de` 110, `name:lld` 35, `alt_name` 206, `loc_name` 72.


* **`ele`**: elevation in metres, 2919 elements (mostly peaks and passes). `source:ele` 34 tells where the elevation comes from.


* **Hut details**: `shelter_type` 686, `operator` 120 (mostly SAT, with several spellings), `capacity` 94, `fireplace` 76, `winter_room` 35, `opening_hours` 44, `reservation` 37, `fee` 91, `access` 136, `website` 119, `phone` 88, `email` 64.


* **Peak details**: `summit:cross` 110, `summit:register` 44, `mountain_pass` 362 (on saddles), `height` 35, `start_date` 93 (mainly 1914 for WWI bunkers), `disused:military` 84.


* **Descriptions**: `description` 85, `description:it` 55, `note` 67, `direction` 137.


* **Links and metadata**: `wikidata` 744, `wikipedia` 221, `importance` 44, `source` 192.


# todo:
- remove timestamp
- divide by natural, tourism, amenity, waterway
- remove prominance, importance, source, wikidata, wikipedia

## suggested todo:
- turn ways and relations into points using `center`
- add an explicit `category` field and make it consistent (peak, saddle/pass, cave, cliff, viewpoint, alpine_hut, wilderness_hut, shelter, waterfall, bunker/ruins, ...), so the types are easy to query
- separate real shelter buildings (`alpine_hut`, `wilderness_hut`, `shelter_type=basic_hut|weather_shelter`) from viewpoints and peaks: `amenity=shelter` (971) mixes huts and small rain shelters
- unify the `operator` spellings ("SAT" and "Società degli Alpinisti Tridentini")
- convert `ele`, `capacity`, `height` into numbers; consider `ele` as an optional field and fill it from a DEM for the 2830 elements without it
- make `fee`, `winter_room`, `fireplace`, `reservation` booleans/enums consistently
- merge `description`/`description:it`/`note` into a single description, and keep `name:it`/`name:de`/`name:lld` as alternative labels
- remove entries without name AND without useful tags (e.g. unnamed cave entrances, which are not hiking destinations)
- link each hut and peak to the trails that pass within about 200 m (using trails.json geometry), and to the municipality
