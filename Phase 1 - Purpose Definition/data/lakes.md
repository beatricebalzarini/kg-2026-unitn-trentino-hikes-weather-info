### Dataset Metadata & Overview

* **Generator and Version**: The data was generated using the Overpass API version 0.7.62.4 and conforms to OSM API version 0.6.


* **Geographical Scope**: The dataset covers significant alpine water features and glaciers across the Trentino-Alto Adige and Lombardy regions of Italy. It includes major lakes (e.g., Lake Garda, Lake Molveno, Lake Caldonazzo) and prominent glaciers (e.g., Marmolada Glacier, Adamello Glacier).


* **Data Structure**: The export consists of 48 OSM elements, composed of two main types: `way` (32 elements) and `relation` (16 elements).


* **Total Counts & Members**: There are 32 `way` elements, which are defined by an array of `nodes` (ordered lists of coordinate IDs) forming closed polygons. The 16 `relation` elements are `multipolygon` structures; instead of raw coordinates, their `members` arrays contain references to other `way` elements, assigning them roles as either `inner` (holes/islands) or `outer` (the main perimeter). Every element includes a `center` object providing a calculated central latitude and longitude point.


* **Timestamps**: The base OSM data timestamp is 2026-11-12T18:26:04Z, and the areas base timestamp is 2026-11-12T17:25:56Z.



### Mandatory Fields & Explanation

Within this specific dataset structure, the following fields are consistently populated across all elements:

* **`type`**: Always specified as either "way" or "relation", dictating the geometric structure of the element.


* **`id`**: A unique numerical identifier assigned to each OSM way or relation (e.g., relation ID 8569 for Lake Garda).


* **`center`**: A calculated coordinate object (`lat` and `lon`) representing the centroid of the lake or glacier.


* **Geometric Constituents**: Depending on the `type`, an element must have either `nodes` or `members` to define its shape:


* **`nodes`**: Mandatory for `way` elements. An ordered array of node IDs that form the closed polygon.


* **`members`**: Mandatory for `relation` elements. An array of references to specific `ways`, categorized by a `role` (either "inner" or "outer") to build complex multipolygons.




* **`tags`**: A collection of key-value pairs defining the attributes of the feature. The following tags are mandatory in this dataset to classify the element:


* **`natural`**: Always present to define the physical feature, set to either `water` (for lakes) or `glacier` (for ice bodies).


* **`name`**: Every lake and glacier in this dataset has a primary name assigned to it.





### Optional Fields & Explanation

The following tags are not universally present, reflecting varying levels of mapper detail, the specific nature of the feature (lake vs. glacier), or regional linguistic variations:

* **`water`**: This tag is used in conjunction with `natural=water` to specify the *type* of water body. When present in this dataset, it is always set to `lake`. It is entirely absent on elements tagged as `natural=glacier`.


* **`type`**: This tag is only mandatory on `relation` elements, where it is always set to `multipolygon` to instruct rendering engines on how to assemble the inner and outer ways. It is absent on `way` elements.


* **Language-specific names (`name:de`, `name:it`, `name:en`, `name:lld`, etc.)**: Given the dataset's location in bilingual/multilingual regions (like South Tyrol and Ladin valleys) and its inclusion of major tourist destinations (like Lake Garda), translations are very common. They are absent on smaller, strictly local features.


* **`alt_name`**, **`old_name:de`**, **`reg_name`**, **`loc_name`**: Provide alternative, historical, regional, or highly localized names (e.g., "Lach de Garda").


* **`ele`**: Elevation in meters above sea level. It is inconsistently applied; some major lakes (like Garda at 65m) and some high-altitude glaciers have it, while others do not.


* **`depth`**: Indicates the depth of the lake (e.g., 6m for Laghetto di Lagorai maggiore). Very rarely mapped.


* **Access and Usage Tags (`boat`, `motorboat`, `ship`, `swimming`, `fishing`, `windsurfing`)**: These tags specify permitted activities. They are mostly found on significant lakes (like Lake Garda or Lake Coredo) to indicate if boating or swimming is allowed/prohibited, but are absent on glaciers or minor alpine tarns.


* **`intermittent`**: A boolean flag (`yes` or `no`) indicating if the water body occasionally dries up.


* **`salt`** and **`tidal`**: Often set to `no` on major freshwater lakes (like Garda or Levico) to explicitly clarify the water type.


* **`wikidata`** and **`wikipedia`**: Links connecting the OSM feature to external knowledge bases. Common on named, prominent lakes and glaciers, but absent on minor unnamed or generic features.