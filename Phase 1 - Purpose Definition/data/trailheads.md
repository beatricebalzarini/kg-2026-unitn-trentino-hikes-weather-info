### Dataset Metadata & Overview

* **Generator and Version**: The data was exported using the Overpass API version 0.7.62.4, conforming to OSM API version 0.6.


* **Geographical Scope**: The dataset covers specific starting points in the Trentino-Alto Adige region of Italy. The coordinates range from approximately latitude 46.01 to 46.43 and longitude 10.87 to 11.84.


* **Data Structure**: The export consists of 3 distinct OSM elements, all of which are of the `node` type. Nodes represent specific single points on the Earth's surface defined by latitude and longitude coordinates.


* **Total Counts**: There are exactly 3 `node` objects.


* **Timestamps**: The base OSM data timestamp is 2026-11-12T18:27:05Z, and the areas base timestamp is 2026-11-12T18:26:04Z.



### Mandatory Fields & Explanation

Within this specific dataset structure, the following fields are consistently populated across all 3 node elements:

* **`type`**: Always specified as "node", indicating the element represents a single geographic point.


* **`id`**: A unique numerical identifier assigned to each OSM node (e.g., 2428330302).


* **`lat` and `lon**`: The precise latitude and longitude coordinates that define the node's location on the map.


* **`tags`**: A collection of key-value pairs defining the attributes of the node. The following tag is mandatory in this dataset to classify the element:


* **`highway`**: Always set to `trailhead`. This explicitly defines the node as a starting point for a trail, path, or route.





### Optional Fields & Explanation

The following tag is applied to the nodes, but is not universally present, reflecting varying levels of mapper detail or the specific nature of the trailhead:

* **`name`**: The designated name of the trailhead (e.g., "Salita al Maso di Agriconda" or "punto di partenza del percorso dei mulini altolinor"). This field is optional and is present on two of the three nodes. Its absence on node 3079089393 implies that the mapper did not know the name, the trailhead does not have an official name, or the information simply hasn't been added to the database yet.