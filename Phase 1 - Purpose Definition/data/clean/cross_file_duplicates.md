# Cross-file duplicates and shared objects

- **Script**: `cleaning/dedup_cross_files.py` (last step of `cleaning/run_all.py`; `--dry-run` only prints the matches)
- **Rewrites in place**: `huts.json`, `accommodations.json`, `food_drink.json`, `landmarks.json`, `cultural_landmarks.json`, `lakes.json`, `glaciers.json`

Each cleaning script already removes the objects that have the **same OSM id** in two source files (e.g. a hut that is also in `amenities.json`). This step handles a different case: the **same real object mapped twice in OSM with two different ids** and ending up in two cleaned files (typically once as a point and once as a building).

## Rule
Two entities are the same object when:
1. they have the **same name** (case-insensitive, spaces normalized; generated labels are never used), and
2. they are **within 100 m** (for lakes and glaciers: within 100 m of the polygon), and
3. they belong to a **compatible pair of files**:

| Kept in (primary) | Removed from (secondary) | Condition on the secondary | Fields copied to the primary when missing |
|---|---|---|---|
| `huts` | `food_drink` | – | `cuisine`, `opening_hours`, `phone`, `email`, `website`, `wikidata`; `food_service = true` |
| `accommodations` | `food_drink` | – | same as above |
| `huts` | `accommodations` | – | `phone`, `email`, `website`, `wikidata`, `opening_hours` |
| `landmarks` | `cultural_landmarks` | category `attraction` or `viewpoint` | `wikidata` |
| `lakes`, `glaciers` | `cultural_landmarks` | category `attraction` or `viewpoint` | `wikidata` |

The kept entity gets `duplicates` = list of `{"osm_id", "file"}` of the removed ones (`null` elsewhere). When `food_service` is set this way, `food_service_source = "duplicate_food_drink"`.

**Not duplicates** (different objects in the same place, kept in both files, useful later as "located at" links): a guidepost named after the hut or pass where it stands, a bus stop or lift station named after a pass, a castle with a restaurant inside, a spring and a fountain.

## Result (52 duplicates removed)
| Pair | Count | Examples |
|---|---|---|
| huts ← food_drink | 6 | Rifugio Petina, Rifugio Orti, Rifugio Scoiattolo, Baita La Zondra, Rifugio Viote, Carlo Valentini |
| accommodations ← food_drink | 41 | Hotel Margherita (its bar and its restaurant), Alt Spaur, Rifugio al Faggio, Hotel Lago Smeraldo, Agritur La Dasa, Castel Vasio, ... |
| huts ← accommodations | 1 | Rifugio Refavaie |
| landmarks ← cultural_landmarks | 2 | Cascate Nardis, Cascata di Rio Revegler |
| lakes ← cultural_landmarks | 2 | Lago di Caldonazzo, Lago di Levico (the same OSM object, also tagged `tourism=attraction`, was in both files) |

**Note on accommodations ← food_drink (41)**: these are mostly a hotel and its restaurant or bar mapped as separate points a few metres apart. They are treated as one entity (the accommodation with `food_service = true`), consistent with the choice already made for huts and guest houses. Fields filled: `food_service` 35, `cuisine` 15, `phone` 6, `opening_hours` 5, `website` 3, `email` 1.

Files after the step: `food_drink` 3004 → 2957, `accommodations` 2348 → 2347, `cultural_landmarks` 4914 → 4910.

## Shared objects (same OSM id in two files, kept in both)
`run_all.py` also checks that ids are unique across files. 13 ids are in two files because the **same OSM object has two roles**. In the KG the id becomes the entity URI, so they become **one entity with two types**. They are listed in `_shared_objects.json`:

| Files | Count | Examples |
|---|---|---|
| ways + aerialways | 4 | Col Rodella, Stalimen - Gardonè, Gardonè - Passo Feudo, Pradel - Rodella: lifts that are stages of bike routes |
| ways + cultural_landmarks | 7 | "Sentiero Forra del Lupo" (3 ways) and "Trincee Austro-Ungariche 1915-18": WWI trenches that are trail segments; "Ponte Forego" (a bridge that is a road segment); "Via Fratelli" |
| landmarks + transport_stops | 1 | Palon: a viewpoint that is also a lift station |
| food_drink + transport_stops | 1 | Bar Tulot: a bar that is also a lift station |
