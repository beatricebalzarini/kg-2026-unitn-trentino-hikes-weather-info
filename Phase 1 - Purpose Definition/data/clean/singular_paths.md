# Cleaning: singular_paths.json — DISCARDED

- **Source**: `data/singular_paths.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Output**: none. The dataset is not used in the KG (user decision).

## Input
11,954 `way` elements (`highway` = path 5357, track 3691, cycleway 2612, footway 276, pedestrian 18), each with `bounds` and full `geometry`.

## Why it is discarded
Overlap of its way ids with the other datasets:

| Way ids of `singular_paths.json` | Count |
|---|---|
| also way members of `trails.json` (→ covered by `data/clean/ways.json`) | 3483 |
| also way members of `mtb.json` (→ covered by `full_stroller_mtb.json`) | 1951 |
| also way members of `stroller.json` | 48 |
| **in no route at all** | **6930** |

1. **No information is lost for the routes**: every way of `singular_paths.json` that belongs to a trail, MTB or foot route is already in `ways.json` or `full_stroller_mtb.json` with the same OSM id. Its geometry is also carried by the route relations themselves.
2. **The other 6930 ways are isolated segments**: they do not belong to any trail. All the CQs ask "which **trails** …", so a segment without a route cannot answer any of them.
3. Keeping it would add 29 MB of geometry and a third copy of the same tags, which raises the risk of inconsistencies between files.
