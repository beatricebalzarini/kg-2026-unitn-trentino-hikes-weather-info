### Dataset Metadata & Overview

* **Generator and Version**: The data was exported using the Overpass API version 0.7.62.4, adhering to OSM API version 0.6.


* **Geographical Scope**: The dataset covers a wide area in northern Italy, with significant clusters around Trento, Rovereto, Riva del Garda, and various alpine valleys (like Val di Fassa and Val di Non).


* **Data Structure**: The export consists exclusively of `node` elements. Nodes represent specific single points on the Earth's surface defined by latitude and longitude coordinates.


* **Total Counts**: There are exactly 126 `node` objects.


* **Timestamps**: The base OSM data timestamp is 2026-11-12T18:11:59Z, and the areas base timestamp is 2026-11-12T17:25:56Z.



### Mandatory Fields & Explanation

Within this specific dataset structure, the following fields are consistently populated across all elements:

* **`type`**: Always specified as "node", indicating the geometric nature of the element as a single point.


* **`id`**: A unique numerical identifier assigned to each OSM node.


* **`lat` and `lon**`: The precise latitude and longitude coordinates that define the node's location on the map.


* **`tags`**: A collection of key-value pairs defining the attributes of the node. The following tags are effectively mandatory in this dataset to classify the element:


* **`amenity`**: Every node has an `amenity` tag, establishing its primary function. The values present in this dataset are `restaurant`, `cafe`, `bar`, `pub`, and `fast_food`.


* **`name`**: Except for a few extremely sparse entries (like node 269348447 which is just a `Bar Esso`), almost every establishment has a designated name.





### Optional Fields & Explanation

The following tags are applied to the nodes to provide rich metadata, but their presence is highly variable and depends entirely on the mapper's diligence and the specific type of establishment:

* **Address Details (`addr:city`, `addr:street`, `addr:housenumber`, `addr:postcode`, `addr:country`)**: Frequently included for urban establishments to allow for geocoding and navigation, but often omitted for rural or alpine locations (like mountain huts).


* **Contact Information (`contact:phone`, `phone`, `contact:website`, `website`, `contact:email`, `contact:facebook`, `contact:instagram`)**: Highly prevalent to facilitate reservations and customer inquiries. The OSM schema allows both the `contact:*` prefix and the standalone keys.


* **`cuisine`**: Describes the type of food served (e.g., `pizza`, `regional`, `italian`, `japanese`, `burger`). Crucial for restaurants and fast-food places, but rarely applied to simple bars or cafes.


* **`opening_hours`**: A complex string defining when the establishment is open. Very useful for users but requires active maintenance to remain accurate.


* **Dietary Accommodations (`diet:vegetarian`, `diet:vegan`, `diet:gluten_free`, `diet:lactose_free`)**: Increasingly common tags indicating if specific dietary needs are catered to (`yes`/`no`).


* **Seating (`outdoor_seating`, `indoor_seating`)**: Indicates if the venue has tables inside or outside.


* **Accessibility (`wheelchair`, `toilets:wheelchair`)**: Indicates if the venue or its toilets are accessible to wheelchair users (`yes`, `no`, or `limited`).


* **Services (`takeaway`, `delivery`, `internet_access`)**: Details additional customer services.


* **Payment (`payment:cash`, `payment:credit_cards`, `payment:lightning`, `currency:XBT`)**: Details accepted payment methods, including a notable presence of cryptocurrency options (Bitcoin/Lightning) in the Trento area.


* **Official References (`ref:vatin`)**: The Italian VAT number (Partita IVA) of the operating business.