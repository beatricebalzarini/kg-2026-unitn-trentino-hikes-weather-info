### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Starting points of trails in Trentino (latitude about 46.01-46.44, longitude about 10.87-11.84).


* **Data Structure**: 3 `node` elements, with `lat`/`lon` and `tags`. It is the smallest dataset.


* **Type**: all have `highway=trailhead`.


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`lat`**, **`lon`**: always "node", OSM id and coordinates.


* **`tags`**: only `highway=trailhead` is always present.


### Optional Fields & Explanation

* **`name`**: 2 of 3 ("Salita al Maso di Agriconda", "punto di partenza del percorso dei mulini altolinor").


* There are no other tags: no `ele`, `operator`, `ref`, parking or route information.


# todo (suggested):
- remove timestamp
- with only 3 elements, this is not enough to be useful: widen the Overpass query (also `information=guidepost` with `hiking=yes`, `amenity=parking` near trails, start nodes of `route=hiking` relations, `public_transport` stops near trails) to build a real set of trailheads
- derive trailheads from trails.json: the first node of the first way of every relation, or the `start` role members and the `from` tag
- give each trailhead a stable `name` (fallback: `from` of the trail) and `ele` (from DEM) so the weather can be linked
- link every trailhead to the closest public transport stop and the closest parking
- decide whether to rename `highway=trailhead` to a `trailhead` class and drop the `highway` tag
