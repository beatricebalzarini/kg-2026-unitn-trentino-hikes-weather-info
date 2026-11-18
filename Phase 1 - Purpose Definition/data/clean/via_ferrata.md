# Cleaning: via_ferrata_routes.json → via_ferrata.json

- **Source**: `data/via_ferrata_routes.json` (Overpass API 0.7.62.4, OSM data © OpenStreetMap contributors, ODbL)
- **Script**: `cleaning/clean_via_ferrata.py` (province rule and length from `cleaning/route_common.py`)
- **Other inputs**: `data/clean/trails.json`, `mtb.json`, `foot_routes.json` (their `main_way_ids` tell which ways are already covered; `ways.json` is not used for this, because it also contains the via ferrata ways themselves)
- **Outputs**:
  - `data/clean/via_ferrata.json`: **26 via ferrata** not already covered by the trails, `kind = "via_ferrata"`
  - `data/clean/via_ferrata_geometry.geojson`: line of every via ferrata
  - their 49 ways are added as segments to `data/clean/ways.json` (see `ways.md`)

## Input
264 elements:
- 29 `relation` with tags but **no `members`** (so no geometry of their own);
- 235 `way` with full geometry: `highway=via_ferrata` 157, `path` 74, `steps` 1, none 3.

## What was already covered
- **22 of the 29 relations are `route=hiking` and are already in `data/clean/trails.json`** (same OSM ids). Nothing to do.
- **149 of the 235 ways are already segments of kept trails** (in `data/clean/ways.json`). Nothing to do.
- In the trails there are already 88 equipped trails (`via_ferrata_scale` set or `cai_scale = EEA`).

The rest (7 relations, 86 ways) describes via ferrata that are **not part of any trail**. They are rebuilt here.

## Method
1. **Group the 86 uncovered ways by normalized name**: lowercase, spaces collapsed, plus explicit aliases for spellings and parts of the same via ferrata:
   - "Magnifici 4" = "Via Ferrata I Magnifici 4"
   - "Via Ferrata Crepa Neigra - Variante prima cima" → "Via Ferrata Crepa Neigra"
   - "Via Ferrata delle Trincee" = "Via ferrata delle trincee" (case only)
2. **Verification (is it really a via ferrata?)**: a group is kept only if the tags prove it is equipped, i.e. at least one of:
   - `highway=via_ferrata` on one of its ways,
   - `via_ferrata_scale` on one of its ways,
   - `safety_rope=yes` on one of its ways,
   - a relation with the same name and `route=via_ferrata`.

   All 28 named groups passed. Short **equipped sections** that are not named "ferrata" ("Canalino del Mulaz": `highway=via_ferrata`, scale 1; "Sentiero delle Stel": `highway=via_ferrata`, `safety_rope=yes`) are kept in the same category (user decision): CQ #19 asks for *equipped* trails.
3. **Match with the relations**: a relation with the same normalized name gives its tags (`via_ferrata_scale`, `duration:forward`) and its id. Matched: Ferrata delle Aquile (6323454), Via Ferrata Magico Alverman al Col Rodella (13281842), Via Ferrata Rino Pisetta (18248702).
4. **Geometry**: the ways of a group are merged (`linemerge`). Length is geodesic. Roundtrip only from geometry when the ways merge into one line (50 m tolerance), else `null`.
5. **Province filter** (same as all the routes, computed on the coordinates): kept if (1) it starts or ends in Trentino, OR (2) at least 50% of its length is in Trentino.

**Limit of the verification**: it is based on the OSM tags only, not on an external source (e.g. SAT or a via ferrata guide).

## Dropped
| What | Count | Why |
|---|---|---|
| "Emergency exit for Ferrata" | 1 way | an escape route, not a via ferrata (user decision) |
| Ways without `name` | 33 | cannot be grouped or labelled (26 of them are `highway=via_ferrata`) |
| Relation without `name` (id 19526452, scale 2, `length=15`) | 1 | cannot be matched with any way |
| Relations without matching ways: "Via Ferrata Val del Rì", "Della Lobbia Alta", "Ferrata Vajo Scuro" | 3 | no geometry: cannot be placed or measured |
| "Laurenzi-Klettersteig - Via Ferrata Laurenzi" | 2 ways | outside the province (32% inside, no endpoint inside) |
| "Maximiliansteig - Via ferrata Maximilian" | 1 way | outside the province (12% inside, no endpoint inside) |

"Laurenzi-Klettersteig" may be the same via ferrata as "Via Ferrata Laurenzi" mapped in two parts. They are kept separate; only the latter is in Trentino.

## Output fields
| Field | Source / transformation | CQ |
|---|---|---|
| `id` | `via_ferrata/<slug of the normalized name>` (groups have no single OSM id) | key |
| `osm_relation_id` | `"relation/{id}"` of the matched relation, else `null` | link to OSM |
| `kind` | constant `"via_ferrata"` | #19 |
| `name` | relation `name`; else the most frequent spelling among the ways, ties broken by the longest | label |
| `name_variants` | the different spellings grouped, when more than one | provenance |
| `wikidata` | relation `wikidata`; else the value on the ways when they all agree (4: Ferrata delle Aquile, Croce di Fai, dei Finanzieri, Rino Pisetta) | external linking (kept wherever present, user decision) |
| `via_ferrata_scale` | relation value; else the highest value among the ways (`3-` < `3` < `3+`) | #19, difficulty |
| `via_ferrata_scale_source` | `relation` 3, `ways_max` 19, `null` 4 | provenance |
| `sac_scale_max` | highest `sac_scale` of the ways, as ordinal 0–6 (same scale as `ways.json`) | difficulty |
| `duration_forward_min` | relation `duration:forward` → minutes (no match had it) | #8 |
| `length_km_computed` | geodesic length of the ways | #18 |
| `roundtrip`, `roundtrip_source` | geometry only (see Method) | #20 |
| `province_rule` | `endpoint` (all 26) | provenance |
| `start`, `end` | endpoints of the line | #11, #17 |
| `main_way_ids` | `"way/{id}"` of the ways of the group → join with `ways.json` | segments |

### Removed
All the other tags of the ways (`surface`, `sac_scale`, `trail_visibility`, `safety_rope`, `via_ferrata`, `cable_number`, `bridge`, `tunnel`, `layer`, `note`, `fixme`, `source`, `bicycle`, `horse`, `motor_vehicle`, ...) are not kept on the via ferrata: the segment-level ones used by the CQs are in `ways.json`. The relation tags not listed above (`network`, `sport`, `climbing`, `length`) are dropped.

## Results
26 via ferrata, 19.2 km in total, 49 ways (`highway=via_ferrata` 32, `path` 15, none 2).

| Via ferrata | Ways | Scale | Length (km) |
|---|---|---|---|
| Canalino del Mulaz (equipped section) | 1 | 1 | 0.199 |
| Ferrata Bolver Lugli | 1 | 3 | 0.671 |
| Ferrata Cengia di Pertica "Giancarlo Biasin" | 1 | 3 | 0.055 |
| Ferrata degli Alpini | 1 | – | 2.544 |
| Ferrata della Miniera dell'Erdemolo | 1 | 2 | 0.558 |
| Ferrata delle Aquile (relation) | 8 | 4 | 0.668 |
| Ferrata di Preore "Sentiero Artpinistico" | 3 | 3 | 0.913 |
| Ferrata Eterna Brigata Cadore (C/D) | 1 | 4 | 1.151 |
| Ferrata Falcipieri | 1 | – | 1.336 |
| Ferrata Monte Roen | 1 | 1 | 0.587 |
| Kaiserjägersteig Col Ombert | 1 | 4+ | 0.137 |
| Sentiero delle Stel (equipped section) | 1 | – | 0.092 |
| Via attrezzata Giulio Segata | 1 | 6 | 0.055 |
| Via Ferrata Carlo Campalani | 1 | 3 | 0.169 |
| Via Ferrata Crepa Neigra (+ variant) | 2 | – | 0.645 |
| Via Ferrata Croce di Fai | 1 | 3 | 0.315 |
| Via Ferrata dei Finanzieri | 2 | 3 | 0.432 |
| Via ferrata delle Bocchette Alte | 1 | 3 | 0.095 |
| Via Ferrata delle Trincee | 12 | 4 | 2.253 |
| Via Ferrata Ernesto Che Guevara | 1 | 3 | 3.288 |
| Via Ferrata Forte Barba di Fior | 1 | 2 | 0.175 |
| Via Ferrata I Magnifici 4 | 2 | 5 | 0.865 |
| Via Ferrata Laurenzi | 1 | 4 | 0.490 |
| Via Ferrata Magico Alverman al Col Rodella (relation) | 1 | 3+ | 0.089 |
| Via Ferrata Marmolada Cresta Ovest | 1 | 3 | 0.829 |
| Via Ferrata Rino Pisetta (relation) | 1 | 5 | 0.578 |

Roundtrip: 3 true, 18 false, 5 unknown.

## Checks
- `id` unique.
- Every via ferrata way is a segment in `ways.json`.

## Notes and open points
- **Border cases**: "Ferrata Eterna Brigata Cadore" (34% of the length inside), "Ferrata Monte Roen" (32%) and "Ferrata degli Alpini" (46%) are kept because one endpoint is inside Trentino (rule 1), even though most of the line is outside.
- Many via ferrata are short (the way covers only the equipped section, not the approach), so `length_km_computed` is the length of the equipped part, not of the whole excursion.
- CQ #19 ("equipped trails") will combine: `kind = "via_ferrata"` OR `via_ferrata_scale` set OR `cai_scale = EEA` (the CAI scale has no "EA" level: T, E, EE, EEA). The via ferrata of this file have no `cai_scale`.
