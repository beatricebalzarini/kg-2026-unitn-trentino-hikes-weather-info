### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Via ferrata (protected climbing routes) and the hiking routes that reach them in Trentino.


* **Data Structure**: 264 elements: 235 `way` (with `bounds` and full `geometry`, on average 37.7 points) and 29 `relation` (with `bounds` and `tags`, but **no `members`**, so they cannot be linked to the ways).


* **Ways** (`highway`): `via_ferrata` 157, `path` 74, `steps` 1. `via_ferrata_scale` 212, `sac_scale` 157 (alpine_hiking 50, demanding_mountain_hiking 38, demanding_alpine_hiking 37, difficult_alpine_hiking 23, ...).


* **Relations** (`route`): `hiking` 22, `via_ferrata` 6, `climbing` 1; all with `type=route`, and `network=lwn` on 23 of the 29.


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`bounds`**: element kind, OSM id and bounding box.


* **`geometry`**: only for the ways.


* **`tags`**: always present.


### Optional Fields & Explanation

* **Difficulty**: `via_ferrata_scale` (0, 1, 1+, 2, 2+, 3-, 3, 3+, 4 ...), `sac_scale`, and for relations `cai_scale` 11 (EEA:F/PD/MD/D).


* **Equipment**: `safety_rope` 20, `via_ferrata` 19 (path, cable, escape), `assisted_trail` 12, `cable_number` 5, `bridge`/`bridge:structure=simple-suspension` 5, `tunnel` 8.


* **Name**: 141 of 264 ("Via Ferrata delle Trincee" 11 ways, "Via ferrata delle Bocchette Alte" 10), `name:de` 15, `name:it`.


* **Relations**: `ref` 12, `osmc:symbol` 12, `operator` 15 (SAT, CAI), `website` 12, `distance` 11 (km), `ascent` 11, `descent`, `duration:forward` 11, `duration:backward`, `from`, `to`, `reg_ref`.


* **Other**: `surface` 79, `trail_visibility` 75, `access` 10, `layer`, `note`, `fixme` 6, `sport` 9, `source` 15, `wikidata` 15.


# todo (suggested):
- remove timestamp
- re-export the 29 relations with their `members` (or `out geom` of relations), otherwise the routes and the 235 ways cannot be linked, and the ways are scattered segments
- link the ways to a named route through `name` as a fallback (e.g. "Via ferrata delle Bocchette Alte" 10 ways)
- split the `via_ferrata` ways from the access `path`/`steps` ways, which are approaches and descents, not the ferrata itself
- normalize the difficulty to a single ordered scale: `via_ferrata_scale` (0-6, with + and -) as the main one, with `cai_scale` EEA:F-D as an alternative
- turn `duration:*` into minutes and `distance` into a number in km, and `safety_rope`/`assisted_trail` into booleans
- remove `fixme`, `note`, `source`, `wikidata`, `osmc:symbol`, `layer`, `bicycle`, `horse`, `motor_vehicle`
- link each via ferrata to the starting hut/trailhead nearby and to the municipality
