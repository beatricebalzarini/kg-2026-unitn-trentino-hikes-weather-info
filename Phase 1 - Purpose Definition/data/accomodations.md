### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Accommodation facilities (`tourism=*`) across Trentino; some of them sit on the Lake Garda shore (e.g. Camping Garda, Camping Brione, Punta Lago).


* **Data Structure**: 617 elements of three kinds: 248 `node` (with top-level `lat`/`lon`), 363 `way` (with `nodes`, the list of node ids, and `center`) and 6 `relation` (with `members` and `center`). No `bounds` or full geometry.


* **Types** (`tourism`): `guest_house` 407, `camp_site` 99, `chalet` 94, `hostel` 17. Within `guest_house`, the `guest_house=*` tag gives the subtype (bed_and_breakfast 58, agritourism 35, guest_house 3, hotel 2, apartment 2).


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id (unique only together with `type`).


* **`tags`**: present in every element. The only tag that is always there is **`tourism`** (the accommodation type).


* **Location**: `lat`/`lon` for nodes; `center.lat`/`center.lon` for ways and relations. A way's `nodes` array only contains ids, not coordinates, so `center` is the only usable position for ways and relations.


### Optional Fields & Explanation

* **`name`**: 567 of 617 (50 elements are unnamed). Some names repeat, e.g. 9 elements called "villaggio - bungalow val Molini".


* **Address** (`addr:street` 309, `addr:housenumber` 304, `addr:city` 283, `addr:postcode` 271, `addr:country` 107, `addr:province` 22, `addr:place`, `addr:hamlet`): partial and inconsistent (province appears both as "TN" and "Trento").


* **Contacts**: `website` 241 and `contact:website` 77, `phone` 202 and `contact:phone` 73, `email` 145 and `contact:email` 73, plus `contact:mobile`, `contact:facebook`, `contact:whatsapp`, `fax`. The same information is split between the plain and the `contact:` keys.


* **Camping services**: `caravans` 87, `tents` 84, `motorhome` 69, `power_supply` 94, `sanitary_dump_station` 37, `shower` 36, `toilets` 34, `drinking_water` 30, `capacity:pitches` 24, `static_caravans`, `cabins`.


* **Rooms and quality**: `stars` 34 (1-5), `rooms` 27, `internet_access` 124, `wheelchair` 56, `dog` 61, `fee` 74, `operator` 55, `ele` 18, `opening_hours` 9.


* **Administrative / noisy tags**: `ref:vatin` 47, `ref:cin` 40 (national accommodation id), `check_date` 40, `source` 27, `building*` (276 elements have `building`, mostly "yes"), plus a few restaurants/hotels with `amenity` (27) and `cuisine` 14.


# todo: 
- treat ways as "nodes"
- delete lake garda
- treat relations as nodes
- nodes -> tourism_accomodation
- remove timestamp
- remove official references

## suggested todo:
- ways and relations carry no point of their own: turn them into points using `center`, so all 617 elements have one `lat`/`lon`
- merge `contact:phone`/`phone`, `contact:email`/`email`, `contact:website`/`website` into single fields
- normalize the values: `power_supply` has `y`, `addr:province` has "TN" and "Trento", `stars`, `rooms` and `capacity:pitches` should become numbers, and yes/no flags should become booleans
- keep `tourism` plus `guest_house` as a two-level category (hotel-like, B&B, agritourism, camp_site, chalet, hostel) instead of a single flat field
- split the camping-only attributes (`tents`, `caravans`, `motorhome`, `capacity:pitches`, ...) from the room-based ones (`rooms`, `stars`)
- drop the 50 unnamed elements or give them a fallback label, and deduplicate repeated names that share the same address
- assign each accommodation to a municipality (point-in-polygon with municipalities.json) and compute the distance to the nearest trailhead
- remove `building*`, `source`, `ref:vatin`, `ref:cin`, `check_date` and `fax` (not useful for hiking)
