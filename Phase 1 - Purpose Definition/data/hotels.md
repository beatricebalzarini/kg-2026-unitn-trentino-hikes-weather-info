### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data. OSM data timestamp: 2026-11-18T12:01:28Z. Data © OpenStreetMap contributors, ODbL.


* **Query** (Overpass Turbo):
  ```
  [out:json][timeout:180];
  area(id:3600045756)->.tn;
  (
    nwr["tourism"~"^(hotel|motel|apartment)$"](area.tn);
  );
  out center;
  ```
  It complements `accomodations.json`, whose query selected only `guest_house`, `camp_site`, `chalet` and `hostel` (see `clean/OPEN_ISSUES.md` #1).


* **Geographical Scope**: Hotels, motels and holiday apartments of the Autonomous Province of Trento (area of relation 45756). All 1765 elements fall inside the province polygon.


* **Data Structure**: 1765 elements of three kinds: 857 `node` (with top-level `lat`/`lon`), 901 `way` (with `nodes`, the list of node ids, and `center`) and 7 `relation` (with `members` and `center`). No `bounds` or full geometry.


* **Types** (`tourism`): `hotel` 1380, `apartment` 381, `motel` 4.


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id (unique only together with `type`).


* **`tags`**: present in every element. The only tag that is always there is **`tourism`** (the accommodation type).


* **Location**: `lat`/`lon` for nodes; `center.lat`/`center.lon` for ways and relations (the `nodes` array of a way only contains ids).


### Optional Fields & Explanation

* **`name`**: 1739 of 1765. Some names repeat (264 elements share their name with another one): chains, or the same hotel mapped twice (point + building).


* **Classification**: `stars` 507 (`3` 308, `4` 98, `3S` 47, `2` 38, `4S` 5, `1` 5, `5` 4, plus `4-5`, `3.5`): the Italian "superior" grade is written as `S`. `rooms` 26, `beds` 2, `capacity` 1.


* **Address** (`addr:street` 870, `addr:housenumber` 850, `addr:city` 788, `addr:postcode` 786, `addr:country` 216, `addr:place` 28): partial, as in the other files.


* **Contacts**: `website` 630 and `contact:website` 134, `phone` 505 and `contact:phone` 140, `email` 367 and `contact:email` 132, `mobile` 29, `fax` 43 and `contact:fax` 97, `contact:facebook` 22. As in the other files, the same information is split between the plain and the `contact:` keys.


* **Services**: `internet_access` 212 (`wlan` 163, `yes` 43, `no` 5), `internet_access:fee` 93, `wheelchair` 108 (`yes` 71, `no` 20, `limited` 17), `smoking` 42, `air_conditioning` 34, `outdoor_seating` 18, `bar` 17.


* **Food**: `amenity` 83 (`restaurant` 64, `hotel` 6, `bar` 5, `cafe` 3, `bar;restaurant`, `restaurant;cafe`), `cuisine` 43.


* **Other**: `operator` 79, `wikidata` 52, `ele` 19.


* **Administrative / noisy tags**: `building` 882, `building:levels` 75, `roof:levels` 39, `roof:shape` 23, `ref:vatin` 120, `check_date` 261, `source` 84, `noaddress` 24.


### Overlaps with the other datasets (same `osm_id`)

* **`amenities.json`**: 73 elements (hotels with a restaurant/bar). In `clean/food_drink.json` they are still present, because the hotels were not cleaned yet.
* **`mixed_pois.json`**: 5 elements; the 4 hotels parked in `clean/_pending_accommodations.json` are all here.
* **`accomodations.json`**, **`huts_landmarks.json`**: none.


# todo (suggested):
- remove timestamp
- clean it with the same rules as `accomodations.json` (`cleaning/clean_accommodations.py`) and merge the result into `clean/accommodations.json` (categories `hotel`, `apartment`, `motel`), so that there is one accommodations file
- normalize `stars`: `3S` → 3 with a `superior` flag (or 3.5), `4-5` and `3.5` to be decided
- apply the same duplicate rule as the other accommodations (same name, same category, within 200 m): many repeated names
- the 73 hotels with a restaurant: keep them only in accommodations (`food_service = true`) and exclude them from `food_drink.json`, as already done for huts and guest houses
- the 4 pending hotels of `mixed_pois.json` are already in this file: drop `_pending_accommodations.json` once this file is cleaned
- remove `building*`, `roof:*`, `ref:vatin`, `check_date`, `source`, `noaddress`, fax and social links, `addr:*` (the municipality comes from the coordinates)
- merge `phone`/`contact:phone`/`mobile`, `email`/`contact:email`, `website`/`contact:website`, as in the other files
