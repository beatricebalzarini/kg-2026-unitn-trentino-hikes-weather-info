### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Hiking route relations (`route=hiking`) of Trentino.


* **Data Structure**: 1657 `relation` elements (1656 `type=route`, 1 `type=superroute`), each with `bounds` and `members` with full `geometry` for ways. It is the largest file (about 87 MB).


* **Networks** (`network`): `lwn` (local) 1479, `rwn` (regional) 86, `nwn` (national) 51, `iwn` (international) 9, `local` 2.


* **Members**: 34125 `way` with empty role, 127 `alternative`, 48 `excursion`, 42 `forward`, 26 `alternative:2`, 23 `connection`, plus 796 `guidepost` nodes and 478 unlabeled nodes.


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`bounds`**: relation kind, OSM id and bounding box.


* **`members`**: ways (with `geometry`) and nodes, with `role`.


* **`tags`**: `route` (always "hiking") and `type` are always present. `network` is on 1627 of 1657.


### Optional Fields & Explanation

* **`ref`**: 1485, the trail number (for example SAT numbers). `reg_ref` 1081 is the regional code.


* **`name`**: only 762 of 1657: most trails are identified by `ref`, not by name.


* **`operator`**: 1362 (mostly SAT, 1133, but also Ecomuseo Argentario 35, CAI 26), with many different spellings.


* **Route description**: `from` 1294, `to` 1294, `distance` 1193, `duration:forward` 1158, `duration:backward` 1107, `ascent` 1146, `descent` 1105, `roundtrip` 125, `stage` 106.


* **Difficulty**: `cai_scale` 1237 (E 886, EE 231, T 42, EEA with sub-grades F/PD/MD/D ~78), `via_ferrata_scale` 22.


* **Signs**: `osmc:symbol` 1428, `symbol` 205, `symbol:it` 207.


* **Links and sources**: `website` 1158, `source` 1218 ("SAT;survey:CAI" and variants), `note:project_page` 1085 (a wiki link, always the same).


* **Other**: `description` (e.g. "Sentiero Italia - Tappa C09"), `importance` 27, `rwn:name`, `network:type` 65, `note` 67, `source:ref` 64.


# todo (suggested):
- remove timestamp
- split by `network` (local/regional/national/international) or by `cai_scale`, as these are the main filters for a hiker
- turn `duration:forward`/`backward` ("HH:MM") into minutes and `distance`, `ascent`, `descent` into numbers; check the units, `distance` is a string in kilometres
- normalize `cai_scale` into a separate numeric/enum difficulty (T, E, EE, EEA, EEA:F/PD/MD/D)
- normalize `operator` (SAT / Società degli Alpinisti Tridentini / SAT Sezione di ...)
- give every trail a usable label: only 762 have a `name`, so build one from `ref` + `from` + `to`
- remove `note:project_page`, `source`, `source:ref`, `osmc:symbol`, `symbol*`, `website`, and long `note`/`description` values
- drop the `members` geometry from the knowledge-graph file (keep it in a separate geometry file) and keep only `bounds`/start point/end point, since 87 MB is too heavy
- keep the 1 `superroute` apart: it groups other routes (Sentiero Italia-like) and should be modelled as a parent route
- link each trail to the trailheads, huts, POIs and municipalities it passes by (spatial join)
