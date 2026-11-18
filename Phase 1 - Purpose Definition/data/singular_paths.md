### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Single path/track/cycleway segments of Trentino, as OSM `way` objects.


* **Data Structure**: 11954 `way` elements, each with `bounds` and a `geometry` array of `lat`/`lon` points (on average 25.6 points per way). There are no `nodes` and no `center`.


* **Types** (`highway`): `path` 5357, `track` 3691, `cycleway` 2612, `footway` 276, `pedestrian` 18.


### Mandatory Fields & Explanation

* **`type`**, **`id`**, **`bounds`**, **`geometry`**: element kind, OSM id, bounding box and line geometry.


* **`tags`**: always present, with `highway` always set.


### Optional Fields & Explanation

* **Surface and quality**: `surface` 9224 (ground 2408, asphalt 2329, gravel 1240, compacted 757, dirt 749, ...), `tracktype` 3517, `smoothness` 1856, `width` 2002, `incline` 1711, `trail_visibility` 2378.


* **Hiking difficulty**: `sac_scale` 4429 (hiking 2303, mountain_hiking 1992, demanding_mountain_hiking 104, alpine_hiking 16, ...).


* **Biking**: `mtb:scale` 9024, `mtb:scale:uphill` 2156, `mtb:scale:imba` 174, `bicycle` 5451, `cycleway` 521.


* **Access**: `foot` 5699, `horse` 1714, `motor_vehicle` 1497, `access` 849, `forestry` 866, `emergency` 857, `designation` 774 (forest road types).


* **Names**: `name` 2381 of 11954, `name:de`, `name:it`.


* **Urban tags**: `lit` 2483, `segregated` 1864, `crossing`, `footway=sidewalk|crossing`, `layer`, `bridge` 484, `tunnel` 133, `wheelchair` 644.


# todo (suggested):
- remove timestamp
- keep only the segments that are useful for hiking: `highway=path|footway|track` for hiking, and `cycleway` only for bike itineraries (split them, since `cycleway` 2612 is mostly urban cycle paths)
- remove urban noise tags: `lit`, `segregated`, `crossing`, `footway`, `layer`, `inline_skates`, `disabled`
- convert `width`, `incline`, `est_width` to numbers, and `sac_scale`/`mtb:scale` to ordered difficulty levels
- keep one difficulty vocabulary for hikes (`sac_scale`) and one for bikes (`mtb:scale`), with the same names as in ways.json
- replace the full `geometry` with a simplified line or length in metres, and compute `length` for each segment
- group segments into the routes of trails.json/mtb.json by `id` membership instead of keeping 12k isolated lines
- assign each segment to a municipality for weather lookup
