### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Restaurants, bars, cafes, fast food and pubs (`amenity=*`) across Trentino.


* **Data Structure**: 3145 elements: 2426 `node` (with `lat`/`lon`), 717 `way` (with `nodes` and `center`) and 2 `relation` (with `members` and `center`: Cantina De Tarczal and Malga Valli).


* **Types** (`amenity`): `restaurant` 1512, `bar` 720, `cafe` 618, `fast_food` 208, `pub` 87.


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id.


* **`tags`**: present in every element; `amenity` is the only tag guaranteed in all 3145.


* **Location**: `lat`/`lon` for nodes, `center` for ways and relations.


### Optional Fields & Explanation

* **`name`**: 2922 of 3145. Many names are generic and repeat ("Bar Centrale" 21, "Bar Sport" 14).


* **Food**: `cuisine` 1035 (multi-valued with `;`), `diet:vegetarian` 141, `diet:vegan` 101, `diet:gluten_free` 32, `takeaway` 188, `delivery` 59.


* **Seating and access**: `outdoor_seating` 818, `indoor_seating` 496, `wheelchair` 378, `smoking` 127, `toilets` 82, `internet_access` 95, `reservation` 39.


* **Opening and payments**: `opening_hours` 778, `payment:*` (credit/debit cards, cash).


* **Address and contacts**: `addr:*` (street 1365, housenumber 1305, postcode 1236, city 1197, country 763), `phone` 594, `contact:phone` 286, `website` 394, `contact:website` 158, `email` 176, `contact:facebook` 152, `contact:instagram` 82.


* **Overlap with huts**: `tourism` is set on 145 elements (hotel 69, `alpine_hut` 47, guest_house 18, ...). These are restaurants that are also hotels or mountain huts, so they duplicate entries of the other datasets.


* **Administrative / noisy tags**: `ref:vatin` 382, `ref:pat:id`, `ref:pat:cat`, `ref:rea_tn`, `ref:it:vat`, `check_date` 397, `check_date:opening_hours` 94, `opening_hours:signed`, `source`, `building` 682.


# todo:
- remove timestamp
- remove official references

## suggested todo:
- turn ways and relations into points using `center`
- keep `amenity` as the category (restaurant, bar, cafe, fast_food, pub) and normalize `cuisine` into a list
- separate the elements with `tourism=alpine_hut|hotel|guest_house` and link them to the accommodation/hut datasets instead of keeping duplicates
- keep only hiking-relevant attributes: `name`, `amenity`, `cuisine`, `opening_hours`, `outdoor_seating`, `wheelchair`, `diet:*`, `website`, `phone`, and one address
- merge `phone`/`contact:phone` and `website`/`contact:website`, and drop the social network links
- remove `check_date*`, `source`, `building`, `opening_hours:signed` (remove the `ref:*` identifiers as already planned)
- flag amenities within a given distance of a trail or trailhead (for example 500 m) so they become useful in the graph
- rename `amenity` to something less generic (e.g. `food_drink`) to avoid clashing with `amenity` in other files
