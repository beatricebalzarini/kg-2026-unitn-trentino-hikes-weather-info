# Elevation enrichment with the Copernicus DEM

- **Scripts**: `cleaning/fetch_dem.py` (download, once) and `cleaning/enrich_dem.py` (steps of `run_all.py` after `build_entities.py`)
- **DEM**: Copernicus DEM GLO-30, 30 m grid (1 arc-second), EPSG:4326, 6 tiles of 1°×1° (N45–N46, E010–E012) chosen automatically from the extent of the entities (some border routes reach 12.5° E); 251 MB, stored in `data/dem/` (in `.gitignore`: download it again with `fetch_dem.py`). Public AWS bucket `copernicus-dem-30m`, no registration.
- **Attribution (required)**: "Copernicus DEM © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by the European Union and ESA; all rights reserved."
- **Validation**: `data/entities/dem_validation.json`

## Why
OSM geometries have no elevation: only some objects carry an `ele` tag. The CQs on height difference (#1, #6), slope (#2, MTB persona) and elevation (#9) need it for every route and point. The DEM gives the elevation of every 30 m cell, so it can be read under every point of a route and of every POI.

The ER model does not change: the DEM **only fills missing values**. The only new attribute, `Route.max_incline_pct`, was already in the ER model as a derived attribute. Provenance fields are added (`ascent_source`, `descent_source`, `max_incline_source`; `ele_source` gets the value `dem`).

## Rules
- **The OSM tag always wins**: a field is filled from the DEM only if it is `null`, and the filled value is marked `dem` in its `*_source` field.
- Where the tag exists, the DEM value is computed **only for comparison** (validation below), never stored.
- The DEM values are read with **bilinear interpolation** of the 4 surrounding cells.

## Method
| What | How | Fields |
|---|---|---|
| **Points** (hospitality, facilities, transport, point landmarks) | DEM at the point | `ele_m`, `ele_source` |
| **Lakes and glaciers** | median of the DEM on a 30 m grid inside the polygon (lake surface is flat; for glaciers it is the middle elevation) | `ele_m`, `ele_source` |
| **Route profile** | every part of the route line resampled every **30 m** (in UTM 32N), DEM read at each sample | – |
| ascent / descent | sum of the elevation changes larger than **15 m** (hysteresis), to ignore DEM noise. Measured from `start` to `end` of the geometry (see Limits) | `ascent_m`, `descent_m`, `ascent_source`, `descent_source` |
| start / end / highest / lowest elevation | DEM at `start` and `end`; highest and lowest sample | `ele_from_m`, `ele_to_m`, `ele_max_m`, `ele_min_m`, `ele_source` (`tag`, `dem` or `tag+dem`) |
| **slope** | profile smoothed with a **150 m moving median**; slope = \|Δz\| / distance over windows of **100 m**; `max_incline_pct` = **95th percentile** of these slopes, i.e. the slope of the steepest stretches (exceeded on only 5% of the route) | `max_incline_pct`, `max_incline_source` |

Routes made of several pieces (lines that do not merge) are processed piece by piece; ascent/descent are summed, highest/lowest taken over all pieces. Routes shorter than 100 m get no slope (7 short via ferrata and trail sections).

### How the parameters were chosen
- **Ascent threshold 15 m**: calibrated on the 542 routes with both OSM `ascent` and `descent`, comparing the total climb (ascent + descent, independent of the direction). Threshold 5 m: median ratio DEM/OSM 1.11, 62% within ±20%; 10 m: 1.05, 72%; **15 m: 1.01, 77%**.
- **Slope as 95th percentile, smoothed**: the plain maximum over 100 m is dominated by DEM artefacts (bridges and viaducts, where the DEM reads the valley floor; trails across steep slopes, where a 30 m cell mixes the slope above and below): median plain maximum of cycle paths 14%, unrealistic. Median of `max_incline_pct` per category with the chosen method: bicycle 5.6%, mtb 20.1%, foot 18.4%, trail 30.7%, via_ferrata 70.6%.

## Result
| File | Field | From OSM tag | From DEM |
|---|---|---|---|
| hospitality.json | `ele_m` | 282 | 5416 |
| facilities.json | `ele_m` | 904 | 5122 |
| transport.json | `ele_m` | 87 | 3898 |
| landmarks.json | `ele_m` | 2693 | 6830 (incl. 110 lakes, all 67 glaciers, 104 peaks) |
| routes.json | `ascent_m` / `descent_m` | 1127 | 630 |
| routes.json | `ele_from/to/max/min_m` | 11 (+20 mixed) | 1726 |
| routes.json | `max_incline_pct` | – | 1750 (7 routes < 100 m) |

Every route and every point now has an elevation.

## Validation (DEM vs OSM tags, `dem_validation.json`)
| Points with an OSM `ele` | n | Median DEM − OSM | Median \|difference\| | Within 25 m |
|---|---|---|---|---|
| alpine huts | 174 | −1.2 m | 4.4 m | 91% |
| wilderness huts | 73 | −0.1 m | 5.1 m | 88% |
| emergency shelters | 97 | +0.6 m | 4.8 m | 91% |
| guideposts | 802 | +2.3 m | 6.8 m | 91% |
| saddles | 647 | −2.8 m | 6.5 m | 85% |
| lift stations | 86 | −1.9 m | 6.0 m | 83% |
| lakes (median inside the polygon) | 50 | −0.7 m | 2.0 m | 90% |
| **peaks** | 1869 | **−21.0 m** | 23.5 m | 52% |

| Routes | Result |
|---|---|
| highest elevation (18 routes with `ele:max`) | median \|difference\| 7.3 m, all within 25 m |
| total climb, ascent + descent (542 routes) | median ratio DEM/OSM 1.01, 77% within ±20% |
| ascent alone, same direction (542) | 26% within ±20% |
| ascent alone, opposite direction (542) | 21% within ±20% |

## Limits
- **Peaks are about 20 m too low**: a 30 m cell smooths the summit. The 1869 peaks with an OSM `ele` keep the tag; only 104 peaks get a DEM value. Route `ele_max_m` of routes reaching a summit can also be some metres too low.
- **Direction of ascent/descent**: OSM `ascent`/`descent` refer to the `from` → `to` direction, the DEM profile to the `start` → `end` of the geometry, which is the opposite for about half of the routes (validation above). For the 630 routes filled from the DEM, `ascent_m` is the climb going from `start` to `end`. The total climb (ascent + descent) does not depend on the direction.
- **Surface model**: GLO-30 is a DSM (radar), so in forests and near buildings it can be some metres above the ground. The comparison with huts, guideposts and saddles (median differences of a few metres) shows that the effect is small for these points.
- `max_incline_pct` is the slope of the steepest stretches at a 100 m scale: short steps or ramps of a few metres are not visible at 30 m resolution.
- Mines (−37 m) and cave entrances (+23 m) differ more: their OSM `ele` is often the elevation of the underground entrance, and they keep the tag.
