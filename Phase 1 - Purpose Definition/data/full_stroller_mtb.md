### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Ways of Trentino that are suitable for strollers and/or mountain bikes (cycleways, tracks, easy roads).


* **Data Structure**: 11415 `way` elements with only `id`, `type` and `tags`. There is no `geometry`, `bounds`, `center` or `nodes`: the elements cannot be placed on a map.


* **Types** (`highway`): `cycleway` 2414, `track` 1790, `unclassified` 1652, `residential` 1393, `tertiary` 1241, `path` 863, `secondary` 585, `primary` 472, `service` 379, `footway` 337, `pedestrian` 225, `living_street` 19, `steps` 10, none 22.


* **Aerialways**: 19 ways are lifts (`aerialway`: gondola 12, chair_lift 5, cable_car 2).


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id.


* **`tags`**: always present; `highway` is set in 11393 of 11415 (the other 22 include the lifts).


### Optional Fields & Explanation

* **Surface and quality**: `surface` 9451 (asphalt 7074, gravel 497, sett 457, ground 215, ...), `smoothness` 1810, `tracktype` 1798, `width` 1192, `incline` 507, `lanes` 1802.


* **Access**: `bicycle` 4434 (designated 2316, yes 1984), `foot` 3390, `horse` 461, `motor_vehicle` 788, `access` 360, `oneway` 2114.


* **Biking difficulty**: `mtb:scale` 877, `mtb:scale:uphill` 338. Hiking: `sac_scale` 640.


* **Urban tags**: `lit` 3476, `segregated` 2067, `cycleway:both` 1560, `cycleway` 682, `sidewalk` 903, `maxspeed` 1648, `lane_markings` 1143, `layer` 1177, `bridge` 856, `tunnel` 311, `crossing` 323, `junction=roundabout` 230.


* **Names and refs**: `name` 6060 ("Ciclovia della Valle dell'Adige" 133), `name:de` 628, `name:it` 577, `ref` 1604 (EV7, SS45bis, ...), `nat_ref` 348, `old_ref` 319.


* **Aerialway tags**: `aerialway:capacity`, `aerialway:duration`, `aerialway:occupancy` on the lifts.


# todo:
- remove timestamp
- divide per highway e aerialway
- remove lit, tracktype, bounds and geometry

## suggested todo:
- this file has no geometry, so the ways cannot be drawn or intersected with municipalities: re-export with `out geom` (or `out center`), or join it with ways.json/singular_paths.json by `id` to get the geometry
- split it into `road/way` (`highway`) and `aerialway` as already planned, and put the 19 lifts together with the cable cars of public_transportation.json
- remove the urban/car tags that do not matter to a stroller or a bike: `maxspeed`, `maxspeed:type`, `lanes`, `lane_markings`, `junction`, `sidewalk`, `layer`, `crossing`
- keep a short quality profile: `surface`, `smoothness`, `width`, `incline`, `bicycle`, `foot`, `wheelchair` and `mtb:scale`
- convert `surface`/`smoothness` into an ordered quality level (for example 1 = best) usable to rank "stroller-friendly" ways
- remove the many `*:etymology*` tags, `source*` and `old_ref`
- check the overlap with ways.json and singular_paths.json (the same `id` can appear in several files): decide which file is the source of truth for geometry and which for attributes
