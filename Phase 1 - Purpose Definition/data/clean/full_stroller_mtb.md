# Cleaning: full_stroller_mtb.json

- **Source**: `data/full_stroller_mtb.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_ways.py`
- **Output**: merged into `data/clean/ways.json` (user decision: one file for all route segments)

**All the rules, fields and results are documented in [`ways.md`](ways.md).**

## Summary for this source
- 11,415 `way` elements, tags only. They are exactly the way members of `mtb.json` + `stroller.json` (100% match on the ids).
- **Kept**: 7611 ways used by the kept bike routes (`mtb.json`) and foot routes (`foot_routes.json`):
  - 5798 added to `ways.json`;
  - 1813 already in `ways.json` because they are also segments of a kept trail. Their tags are identical in the two sources (checked).
- **Dropped**: 3804 ways of routes that were not kept.
- **Lifts**: 19 aerialways in the source. The 13 used as stages of kept bike routes are kept as segments with the `aerialway` field set; the other 6 are dropped.
- New value mappings needed only by this source: `surface` `metal grid` → `metal_grid`, `rubber` → `paved`; `bicycle` `official` → allowed, `unknown` → null.
