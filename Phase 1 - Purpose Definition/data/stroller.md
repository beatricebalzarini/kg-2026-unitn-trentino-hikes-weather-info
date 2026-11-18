### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Stroller-friendly itineraries, mostly near Trento, Andalo and Imèr.


* **Data Structure**: 13 `relation` elements (`route=foot`), each with `bounds` and `members` with `geometry` on the ways. Members: 553 `way` (1 `forward`), 56 `node` (including 1 `start` and 1 `stop`).


* **Networks** (`network`): `lwn` 9 (the other 4 have none).


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`bounds`**, **`members`**: relation kind, OSM id, bounding box and members.


* **`tags`**: `route` ("foot") and `type` ("route") are always set.


### Optional Fields & Explanation

* **`name`**: 12 of 13.


* **Description**: `description` 2, `from` 2, `to` 2, `roundtrip` 1, `ref` 1 ("SAT O281"), `historic` 1.


* **Operators and links**: `operator` 2, `website` 3, `url` 1, `wikidata` 2, `wikipedia` 2, `network:type` 2.


# todo (suggested):
- remove timestamp
- this is a very small file (13 routes): check that the Overpass query really selects strollers. Nothing in the tags says that a route is stroller-friendly (the stroller filter lives only in the query), so add an explicit `stroller_friendly=yes` flag
- complete the missing data (distance, duration, surface), which is nearly absent: compute the length from the geometry and the surface from the member ways
- check for `wheelchair`/`stroller` tags on the member ways and use them to validate the selection
- remove `wikidata`, `wikipedia`, `url`, `website` if not needed and keep only `name`, `description`, `from`, `to`, `roundtrip`
- give a common schema with trails.json (same `distance`, `duration`, `ascent` fields) so they can be merged as one `Route` class with a `kind`
