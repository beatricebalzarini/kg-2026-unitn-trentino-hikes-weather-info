### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: General set of paths, tracks and roads of Trentino used for hiking, as OSM `way` objects.


* **Data Structure**: 26507 `way` elements, only `id`, `type` and `tags` (no `geometry`, `bounds`, `center` or `nodes`). One way has no tags.


* **Types** (`highway`): `path` 9806, `track` 7390, `unclassified` 2568, `residential` 2237, `tertiary` 1006, `footway` 855, `service` 746, `secondary` 554, `cycleway` 349, `primary` 319, `steps` 312, `pedestrian` 158, `via_ferrata` 148, none 21.


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id.


* **`tags`**: present in all but one element; `highway` is set in 26486.


### Optional Fields & Explanation

* **Surface and quality**: `surface` 15922, `tracktype` 6304, `smoothness` 2131, `width` 2133, `incline` 2017, `trail_visibility` 3987.


* **Hiking difficulty**: `sac_scale` 8398 (mountain_hiking 4442, hiking 2717, demanding_mountain_hiking 854, alpine_hiking 234, ...).


* **Access**: `bicycle` 5173, `foot` 5033, `horse` 1958, `motor_vehicle` 2228, `mtb:scale` 4565, `mtb:scale:uphill` 1594, `emergency` 950, `forestry` 941, `designation` (forest road types).


* **Roads**: `ref` 1627 (SP31, SS241, ...), `maxspeed` 1051, `lanes` 1349, `oneway` 1022, `lit` 3063, `bridge` 1351, `tunnel` 235, `sidewalk`, `service`.


* **Winter**: `piste:type` (nordic 116, downhill 39, hike 20, sled 11, ...).


* **Names and sources**: `name` 8318 (many repeated, "Ciclovia della Valsugana" 64), `source` 1629 ("SAT;survey:CAI", "www.sat.tn.it", ...).


# todo (suggested):
- remove timestamp
- this file has no geometry: re-export with `out geom` (or `out center`) or join it with singular_paths.json by `id`; otherwise the ways cannot be used spatially
- split by `highway` into hiking paths (`path`, `footway`, `steps`, `via_ferrata`), tracks (`track`), roads (`unclassified`, `residential`, `service`, `tertiary`, `secondary`, `primary`) and cycleways
- drop the road-only ways (`residential`, `service`, `tertiary`, `secondary`, `primary`, `unclassified`, about 7400) unless they are needed for access to trailheads
- remove `maxspeed`, `lanes`, `oneway`, `lit`, `sidewalk`, `lane_markings`, `service`, `cycleway:both`, `piste:type` and the many tags useful only for car routing
- normalize `sac_scale`, `mtb:scale`, `trail_visibility`, `smoothness`, `surface` into ordered levels, and `width`/`incline` into numbers
- use `designation` (IT-TN forest road types A/B/L) as a separate attribute for forest roads, and give a clear label to the 21 ways without `highway`
- decide the overlap with singular_paths.json and full_stroller_mtb.json (same ways in several files)
