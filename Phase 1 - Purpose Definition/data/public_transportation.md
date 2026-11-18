### Dataset Metadata & Overview

* **Generator and Version**: Overpass API 0.7.62.4, OSM API version 0.6. The JSON root has `version`, `generator`, `osm3s` and `elements`; only `elements` holds data.


* **Geographical Scope**: Public transport of Trentino: bus stops, railway stations, bus stations and cable cars/lifts, around Trento, the valleys (Val di Fassa, Val di Non) and the Garda area.


* **Data Structure**: 4948 elements: 4624 `node` (with `lat`/`lon`), 322 `way` (with `nodes` and `center`) and 2 `relation` (with `members` and `center`: Rovereto, a `stop_area`, and Cles - Piazza Fiera, a multipolygon).


* **Categories** (`public_transport`): `platform` 4021, `station` 408, `stop_position` 32, `stop_area` 1; 486 elements have none.


* **Bus**: `highway=bus_stop` 4032, `bus=yes` 3266, `amenity=bus_station` 19.


* **Rail**: `railway=station` 54, `railway=halt` 17, `train` 61, network "Ferrovia Trento-Malé-Mezzana" 37.


* **Lifts**: `aerialway` is set on 794 elements: `station` 582, `chair_lift` 139, `gondola` 55, `cable_car` 15.


### Mandatory Fields & Explanation

* **`type`**, **`id`**: element kind and OSM id.


* **`tags`**: always present.


* **Location**: `lat`/`lon` for nodes, `center` for ways and relations.


### Optional Fields & Explanation

* **`name`**: 4470 of 4948 (478 without name, mainly platforms).


* **Operator and network**: `operator` 661 (Trentino Trasporti with many spellings, RFI, ATV, DolomitiBus), `network` 141, `ref` 394, `route_ref` 38.


* **Services at the stop**: `shelter` 2324, `bench` 1620, `bin` 1209, `lit` 1003, `tactile_paving` 1223, `wheelchair` 408, `departures_board` 239, `internet_access` 32.


* **Lifts**: `aerialway:capacity` 153, `aerialway:occupancy` 191, `aerialway:duration` 124, `aerialway:bubble` 68, `aerialway:heating` 49, `aerialway:access` 99, `aerialway:summer:access` 128, `aerialway:station` 65.


* **Other**: `ele` 90, `wikidata` 68, `wikipedia` 55, `building` 93, `oneway` 39, `bicycle` 35, `source` 105, `note` 36, `name:it` 35, `alt_name` 32, `check_date:shelter` 128.


# todo (suggested):
- remove timestamp
- split the file by mode: bus stops, railway stations, bus stations and lifts (`aerialway`), because their attributes and use are different
- keep the `public_transport` tag as the type (stop vs. platform vs. station) and avoid counting the same stop twice (platform + stop_position + station nodes)
- turn ways and relations into points using `center`
- normalize `operator` ("Trentino Trasporti", "Trentino trasporti S.p.A.", "Trentino trasporti", ...)
- drop the 478 elements without name, or give them a fallback name; they are mostly platforms
- remove stop-furniture tags that are not needed (`bench`, `bin`, `shelter`, `tactile_paving`, `lit`, `check_date:shelter`, `source`, `note`)
- move the `aerialway` lifts to the same class as the ones in full_stroller_mtb.json, and keep `aerialway:capacity|duration|occupancy` as numbers
- add the distance of each stop to the nearest trailhead and trail, and the municipality (point-in-polygon)
- remove `wikidata`, `wikipedia`, `building`
