### Dataset Metadata & Overview

* **Generator and Version**: The data was exported using the Overpass API version 0.7.62.4, adhering to OSM API version 0.6.


* **Geographical Scope**: The dataset covers the mountainous areas of northern Italy, particularly around Trentino, Lake Garda, and the Stelvio National Park region.


* **Data Structure**: The export consists of 99 OSM elements of varying geometric types: 47 `node` elements, 47 `way` elements, and 5 `relation` elements.


* **Total Counts & Members**:
* **Nodes (47)**: Represent single points on the map, usually defining smaller or less detailed properties (e.g., a specific B&B building).


* **Ways (47)**: Formed by an ordered list of nodes, these define the footprint of a building or the perimeter of a smaller campground.


* **Relations (5)**: Complex `multipolygon` structures used to define the boundaries of large features (in this case, large campsites and Lake Garda itself, which seems to have been caught in the query bounding box).




* **Timestamps**: The base OSM data timestamp is 2026-11-12T18:14:00Z, and the areas base timestamp is 2026-11-12T17:25:56Z.



### Mandatory Fields & Explanation

Within this specific dataset structure, the following fields are consistently populated depending on the element type:

* **`type`**: Always specified as "node", "way", or "relation", dictating the geometric structure of the element.


* **`id`**: A unique numerical identifier assigned to each OSM element.


* **Geometric Constituents**:
* `node` elements strictly contain `lat` and `lon` coordinates.


* `way` elements strictly contain an array of `nodes` (node IDs) and a calculated `center` coordinate.


* `relation` elements strictly contain an array of `members` (way references) and a calculated `center` coordinate.




* **`tags`**: A collection of key-value pairs defining the attributes of the feature. The following tag is effectively mandatory to classify the accommodation:


* **`name`**: Every accommodation facility in this dataset has a designated name.


* **Primary Classification Tag**: Almost every element features a primary tag defining its purpose, most commonly `tourism=guest_house`, `tourism=camp_site`, `tourism=chalet`, or `tourism=hostel`. (Note: Lake Garda is tagged `natural=water` but was included in the dataset likely due to spatial overlap with a campsite query).





### Optional Fields & Explanation

The following tags are applied to the elements to provide rich metadata, but their presence is highly optional and depends entirely on the mapper's diligence and the specific type of accommodation:

* **Address Details (`addr:city`, `addr:street`, `addr:housenumber`, `addr:postcode`)**: Frequently included for urban or village-based guest houses and B&Bs, allowing for geocoding and navigation. Often omitted for remote alpine chalets or rural campsites.


* **Contact Information (`contact:phone`, `contact:website`, `contact:email`, `phone`, `website`, `email`)**: Highly prevalent for commercial accommodations like hotels and campsites to facilitate bookings. The OSM schema allows both the `contact:*` prefix and the standalone keys, and both are used interchangeably here.


* **Sub-classification tags (`guest_house=bed_and_breakfast`, `guest_house=agritourism`)**: Used to further specify the exact nature of a generic `tourism=guest_house` tag.


* **Camp Site Attributes (`tents`, `caravans`, `motorhome`, `power_supply`, `shower`, `sanitary_dump_station`, `fee`, `dog`)**: A rich set of boolean (`yes`/`no`) tags applied specifically to `tourism=camp_site` features to detail the available amenities and rules.


* **`internet_access`**: Indicates the availability of Wi-Fi (usually tagged as `wlan`), often accompanied by `internet_access:fee` to indicate if it is free or paid.


* **`wheelchair`**: Indicates accessibility for wheelchair users (`yes`, `no`, or `limited`).


* **`building=yes`**: Often applied to `way` elements to indicate that the polygon represents the physical footprint of the building housing the accommodation.


* **Official References (`ref:vatin`, `ref:cin`)**: VAT numbers or Regional Identification Codes (CIN) used in Italy to officially identify registered tourist accommodations.