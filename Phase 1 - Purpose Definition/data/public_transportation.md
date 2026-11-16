### Dataset Metadata & Overview

* **Generator and Version**: The data was exported using the Overpass API version 0.7.62.4, conforming to OSM API version 0.6.


* **Geographical Scope**: The dataset covers a wide area in northern Italy, heavily featuring the city of Trento and its suburbs, as well as alpine valleys (like Val di Fassa and Val di Non) and the area around Riva del Garda.


* **Data Structure**: The export consists exclusively of `node` elements. In OSM, a node represents a specific single point on the earth's surface defined by latitude and longitude.


* **Total Counts**: There are exactly 249 `node` objects included in this extract.


* **Timestamps**: The base OSM data timestamp is 2026-11-12T18:22:05Z, and the areas base timestamp is 2026-11-12T17:25:56Z.



### Mandatory Fields & Explanation

Within this specific dataset structure, the following fields are consistently populated across all elements:

* **`type`**: Always specified as "node", indicating the geometric nature of the element as a single point.


* **`id`**: A unique numerical identifier assigned to each OSM node.


* **`lat` and `lon**`: The precise latitude and longitude coordinates that define the node's location on the map.


* **`tags`**: A collection of key-value pairs defining the attributes of the node. Because this dataset is a mixed collection of transport POIs, there isn't one single mandatory tag for every node, but every node has at least one primary feature tag. The most common primary tags are:


* **`highway=bus_stop`**: The most prevalent tag in the dataset, used to identify bus stops.


* **`aerialway=station`**: Used extensively to identify cable car, gondola, and chairlift stations, common in the alpine regions.


* **`railway=station` or `railway=halt**`: Used to identify train stations (e.g., along the Ferrovia Trento-Malé-Mezzana).





### Optional Fields & Explanation

The following tags are applied to the nodes to provide rich metadata, but their presence is highly variable depending on the specific type of transport feature and the mapper's level of detail:

* **`name`**: The designated name of the station or stop (e.g., "Trento Santa Chiara", "Paolina"). It is present on almost all nodes but is technically optional in the OSM schema.


* **`public_transport`**: Often used alongside the primary tags to clarify the role in the public transport network (e.g., `public_transport=platform`, `public_transport=station`, `public_transport=stop_position`).


* **Amenities (`shelter`, `bench`, `bin`, `lit`)**: Highly common on `highway=bus_stop` nodes to indicate if the stop has a roof, seating, a trash can, or street lighting (`yes` or `no`).


* **Accessibility (`wheelchair`, `tactile_paving`)**: Indicates if the stop or station is accessible to wheelchair users (`yes`, `no`, or `limited`) and if it has tactile paving for the visually impaired.


* **Aerialway Specifics (`aerialway:access`, `aerialway:summer:access`, `aerialway:station`)**: Detail whether an aerialway station allows boarding (`entry`), alighting (`exit`), or both, and whether it operates in the summer.


* **Network & Operator (`network`, `operator`)**: Identify the transport company or system (e.g., "Trentino Trasporti", "Rete Ferroviaria Italiana").


* **`ele`**: Elevation in meters above sea level, frequently added to alpine aerialway stations.