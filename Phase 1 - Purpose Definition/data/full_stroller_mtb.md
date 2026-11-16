### Dataset Metadata & Overview

* **Generator and Version**: The export was created by the Overpass API version 0.7.62.4, using OSM API version 0.6.


* **Geographical Scope**: The dataset covers an extensive region in the Italian Alps (Trentino-Alto Adige and Veneto), including areas around Riva del Garda, the Fiemme and Fassa valleys, and the Brenta Dolomites. It captures a wide variety of routes from urban paths to high-altitude via ferratas.


* **Data Structure**: The provided subset contains 180 distinct OSM elements, all of which are of the `way` type (representing linear features like paths, roads, and aerialways).


* **Total Counts & Members**: There are 180 `way` objects. Only a portion of these ways have their coordinate `geometry` arrays and `bounds` fully resolved in this subset, while others (especially the initial elements) are truncated and only display their ID and tags.


* **Timestamps**: The base OSM data timestamp is 2026-11-12T18:08:59Z.



### Mandatory Fields & Explanation

Within this specific dataset structure, the following fields are consistently populated across all way elements:

* **`type`**: Always specified as "way", indicating the element is a linear path formed by connected nodes.


* **`id`**: A unique numerical identifier assigned to each OSM way (e.g., 4702282 for the Canazei - Pecol gondola).


* **`tags`**: A collection of key-value pairs defining the attributes of the path. While the specific tags vary, the `tags` object itself is always present, containing at least one primary classification tag:


* **`highway`** or **`aerialway`**: Every element in this list contains one of these two foundational tags to classify the type of route. `highway` is used for roads, cycleways, tracks, paths, and via ferratas, while `aerialway` is used for cable cars, gondolas, and chairlifts.





### Optional Fields & Explanation

The following tags and fields are not universally present, reflecting varying levels of mapper detail or specific physical characteristics of the routes:

* **`bounds`** and **`geometry`**: These fields (providing the bounding box and the explicit coordinate points of the path) are only present for the later elements in the list (starting from ID 26141700). The earlier elements are truncated, showing only their tags.


* **`name`** / **`alt_name`** / **`name:de`** / **`name:it`**: The name of the route (e.g., "Ciclovia della Valle dell'Adige"). Absent on minor tracks or residential streets where a name is either unknown or doesn't exist. Regional language tags are common in bilingual areas.


* **`surface`**: Describes the physical ground type (e.g., `asphalt`, `gravel`, `sett`, `rock`, `ground`). Highly relevant for cycling and hiking, but sometimes omitted by mappers.


* **`sac_scale`** / **`mtb:scale`** / **`mtb:scale:uphill`** / **`via_ferrata_scale`**: These scales indicate the difficulty of the route for hikers, mountain bikers, and climbers respectively. They are only present on routes where such activities are relevant and when the mapper has specifically assessed the difficulty.


* **Routing and Access Tags (`bicycle`, `foot`, `motor_vehicle`, `horse`, `psv`)**: Used to explicitly grant or deny access (e.g., `bicycle: designated`, `motor_vehicle: no`). Often used to differentiate dedicated cycleways from shared paths.


* **`tracktype`**: Used on `highway=track` to indicate the firmness of the surface (grade1 to grade5).


* **`lanes`** / **`oneway`** / **`maxspeed`**: Traffic management tags commonly applied to roads (e.g., `highway=primary` or `residential`) but rarely to paths or cycleways.


* **`lit`**: Indicates whether the route has street lighting.


* **`bridge`** / **`tunnel`** / **`layer`**: Used to indicate when a path crosses over or under another feature or the natural terrain.


* **`aerialway` attributes (`capacity`, `duration`, `occupancy`)**: Specific metadata applied only to aerialways like gondolas and chairlifts to describe their operational capacity.