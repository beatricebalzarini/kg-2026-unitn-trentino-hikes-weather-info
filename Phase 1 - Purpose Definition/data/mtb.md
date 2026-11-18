### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Mountain-bike and cycling routes of Trentino.


* **Data Structure**: 144 `relation` elements (route relations), each with `bounds` and a `members` array where every way carries its full `geometry` (`lat`/`lon` points). This is why the file is about 20 MB.


* **Route types** (`route`): `mtb` 91 and `bicycle` 53. The `bicycle` ones are mostly cycle paths (ciclovie), the `mtb` ones are trails for mountain bikes.


* **Networks** (`network`): `lcn` 47, `ncn` 25, `rcn` 20, `mtb` 11, `lwn` 5, `icn` 1; 35 relations have none.


* **Members**: 12785 `way` with empty role, 1137 `forward`, 487 `backward`, plus 49 `guidepost` and 48 unlabeled `node` members.


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`bounds`**: relation kind, OSM id and bounding box.


* **`members`**: list of ways (with `geometry`) and nodes, each with `role`.


* **`tags`**: always `route` (mtb or bicycle) and `type` ("route").


### Optional Fields & Explanation

* **`name`**: 111 of 144. 23 of them are stages of the same itinerary, "SICAI Ciclo" (`ref` "SI-C", with `stage`, `cai_scale:mtb` MC/OC and `date`).


* **`ref`** 105, **`network`** 109, **`operator`** 53 (tourist boards, Comune di Trento, Provincia Autonoma di Trento), **`cycle_network`** 14 ("bicipolitana Trento", EuroVelo).


* **Route description**: `from` 51, `to` 51, `via`, `roundtrip` 25, `oneway` 12, `distance` 23, `ascent` 8, `descent` 5, `length` 2.


* **Difficulty**: `cai_scale:mtb` and `cai_scale:mtb:uphill` 23, `mtb:scale` 8 (1-3), `mtb:type` 8 (crosscountry, freeride, allmountain, ...).


* **Names in other languages**: `name:de` 8, `name:it` 8, `operator:de`, `operator:it`.


* **Links and metadata**: `website` 25, `wikipedia` 8, `wikidata` 6, `colour` 32, `osmc:symbol` 6, `source` 24, `note` 15, `fixme` 6, `description` 5, `state` 2 ("proposed").


# todo:
- remove timestamp
- divide between btm and cliclovie

## suggested todo:
- divide between MTB (`route=mtb`) and cycleways/cycle routes (`route=bicycle`, "ciclovie") as already planned: they are different kinds of activity
- use `network` as a level: `icn`/`ncn` (international/national), `rcn` (regional), `lcn` (local), `mtb`
- unify the 23 "SICAI Ciclo" relations into one parent route with 23 stages (`stage` is already there)
- convert `distance`, `length`, `ascent`, `descent` to numbers in one unit (kilometres and metres); `distance` is in km as text ("4.070") in other files
- keep only the difficulty fields useful for a user (`mtb:scale`, `cai_scale:mtb`, `mtb:type`), and convert `roundtrip`/`oneway` to booleans
- remove `fixme`, `note`, `osmc:symbol`, `colour`, `source`, `state=proposed` (proposed routes do not exist yet)
- compute the length from the geometry for the routes that do not have `distance`
- simplify the member geometry (or keep only `bounds` and a centroid) to reduce the 20 MB, and avoid the very long `members` arrays
- link routes to the municipalities they cross and to the trailheads/public transport near their start
