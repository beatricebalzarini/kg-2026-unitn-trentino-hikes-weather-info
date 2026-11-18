### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data. OSM data timestamp: 2026-11-18T12:02:28Z. Data © OpenStreetMap contributors, ODbL.


* **Query** (Overpass Turbo):
  ```
  [out:json][timeout:180];
  area(id:3600045756)->.tn;
  (
    nwr["amenity"="parking"](area.tn);
  );
  out center;
  ```
  Optional dataset: it is needed only if trailheads are built later as "route endpoints near a car park / stop / hut / village" (option B in `clean/trailheads.md`; the current decision is option C, no trailhead entity).


* **Geographical Scope**: Car parks of the Autonomous Province of Trento (area of relation 45756). 10,855 of 10,857 fall inside the province polygon.


* **Data Structure**: 10,857 elements: 1582 `node` (with `lat`/`lon`), 9197 `way` (with `nodes` and `center`) and 78 `relation` (with `members` and `center`). No `bounds` or full geometry.


* **Types** (`parking`): `surface` 6739, `street_side` 1588, `lane` 264, `underground` 74, `rooftop` 42, `multi-storey` 38, `layby` 8, `carports` 3; 2099 without `parking`.


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id (unique only together with `type`).


* **`tags`**: present in every element; **`amenity=parking`** is always set.


* **Location**: `lat`/`lon` for nodes; `center` for ways and relations.


### Optional Fields & Explanation

* **Access**: `access` 6685 (`yes` 2768, `private` 1927, `customers` 1752, `permissive` 84, `no` 83, `permit` 55, ...). Private and customer car parks (shops, hotels, condominiums) are a large share.


* **Fee**: `fee` 4384 (`no` 3850, `yes` 523, plus a few opening-hours-like values such as "Jul-Aug: 08:00-18:00"), `fee:conditional` 19, `charge` 47, `maxstay` 150.


* **Size and surface**: `capacity` 1789 (mostly small: 1–6 places are the most frequent values), `capacity:disabled` 651, `capacity:women` 34, `capacity:parent` 32; `surface` 2934 (`asphalt` 1675, `paved` 438, `gravel` 201, `unpaved` 161, ...).


* **Other**: `name` 423 (few car parks are named), `operator` 227, `operator:type` 105, `supervised` 257, `park_ride` 123 (`yes` 25), `opening_hours` 58, `wheelchair` 103, `covered` 29.


* **Noisy tags**: `orientation` 249, `layer` 93, `lit` 81, `level` 33, `maxheight` 21, `hgv` 25, `building` 20, `addr:*`, `check_date*`, `source`, `description`, `ref`, `area`.


# todo (suggested):
- remove timestamp
- use only if trailheads are built (option B); otherwise this file is not needed for the CQs
- keep only the car parks useful to hikers: drop `access` = private / customers / no / permit, and probably `street_side` / `lane` (parking along urban streets), keeping `surface`, `underground`, `multi-storey`, `layby` and the ones near a route endpoint
- keep few fields: `name` (fallback generated from the municipality), `parking` type, `fee` (normalized to boolean, the opening-hours-like values moved apart), `capacity` (integer), `park_ride`, `wheelchair`, position, municipality
- remove `orientation`, `layer`, `lit`, `level`, `maxheight`, `hgv`, `building`, `addr:*`, `check_date*`, `source`, `capacity:women`, `capacity:parent`
