### Dataset Metadata & Overview

* **Generator and Version**: The data was exported using the Overpass API version 0.7.62.4, using OSM API version 0.6.


* **Geographical Scope**: The dataset covers the mountainous regions of Trentino-Alto Adige and Lombardy in northern Italy, including areas like the Brenta Dolomites, the Adamello-Presanella Alps, and the Lagorai chain.


* **Data Structure**: The export consists of 229 distinct OSM elements, all of which are of the `node` type (representing specific single points on the Earth's surface).


* **Total Counts & Members**: There are 229 `node` objects. Because they are nodes, each element contains a single latitude (`lat`) and longitude (`lon`) coordinate pair instead of the `geometry` arrays found in `way` elements.


* **Timestamps**: The base OSM data timestamp is 2026-11-12T17:47:27Z, and the areas base timestamp is 2026-11-12T17:25:56Z.



### Mandatory Fields & Explanation

Within this specific dataset structure, the following fields are consistently populated across all 229 node elements:

* **`type`**: Always specified as "node", indicating a single point defined by a specific coordinate pair.


* **`id`**: A unique numerical identifier assigned to each OSM node (e.g., 26862538 for Becco di Filadonna).


* **`lat` and `lon**`: The precise latitude and longitude coordinates that define the node's location on the map.


* **`tags`**: A collection of key-value pairs defining the attributes of the node. While the specific tags vary wildly, the `tags` dictionary itself is always present, containing at least one primary classification tag. The most common primary tags in this dataset are:


* **`natural`**: Used to classify the physical geography (e.g., `peak`, `saddle`, `cave_entrance`, `cliff`).


* **`tourism`**: Used to classify human-oriented features (e.g., `viewpoint`, `alpine_hut`, `wilderness_hut`, `information`).


* **`amenity`**: Used for facilities (e.g., `shelter`, `bench`, `restaurant`).


* **`waterway`**: Used to identify water features (e.g., `waterfall`).





### Optional Fields & Explanation

The following tags are not universally present, reflecting varying levels of mapper detail, regional naming conventions, or the specific physical characteristics of the landmarks:

* **`name`** / **`alt_name`** / **`name:de`** / **`name:it`** / **`name:lld`**: The name of the feature. While almost always present, it is occasionally absent (e.g., id 388120131, which only has the tag `natural=peak`). Regional language tags (German, Italian, Ladin) are very common in this bilingual/trilingual alpine area.


* **`ele`**: Elevation in meters above sea level. Crucial for alpine features like peaks and passes, but generally absent from viewpoints, waterfalls, and caves.


* **`mountain_pass`**: A boolean flag (`yes`) frequently appended to `natural=saddle` nodes to confirm they are actively used as passes by hikers or vehicles.


* **`summit:cross`** and **`summit:register`**: Boolean flags indicating the presence of a summit cross (a common feature on alpine peaks) and a summit register (guestbook).


* **`prominence`**: The topographic prominence of a peak in meters. Only occasionally mapped for significant mountains.


* **`importance`**: A subjective tag (e.g., `regional`, `urban`, `local`) sometimes used by mappers to dictate at what zoom level a peak label should be rendered on a map.


* **`source`** / **`source:ele`** / **`source:prominence`**: Metadata indicating where the mapper derived the name or elevation (e.g., "3rd Military Mapping Survey of Austria-Hungary", "Kompass 626 map").


* **`wikidata`** and **`wikipedia`**: Links to corresponding Wikidata entities and Wikipedia articles, connecting the OSM node to external knowledge bases.


* **Hut Attributes (`shelter_type`, `fee`, `open`, `phone`, `website`)**: Specific metadata applied only to shelters and alpine huts to describe their facilities and contact information.