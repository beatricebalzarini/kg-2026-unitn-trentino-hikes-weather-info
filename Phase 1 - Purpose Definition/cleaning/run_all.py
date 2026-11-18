"""Run the whole OSM cleaning pipeline in the right order, then check the result.

Usage (from the repository root):
    .venv/bin/python "Phase 1 - Purpose Definition/cleaning/run_all.py"

The order matters: several scripts read the outputs of the previous ones (see STEPS).
At the end it checks, on data/clean/:
  - ids unique inside every file AND across files (an id will become a URI in the KG);
  - referential integrity (way ids, guidepost ids, municipality codes, province members);
  - prints a summary and a hash of every output, so two runs can be compared.
"""
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLEAN = HERE.parent / "data" / "clean"

STEPS = [  # (script, what it needs)
    ("clean_province_boundaries.py", "raw province + municipalities"),
    ("clean_municipalities.py", "province_boundary.geojson"),
    ("clean_trails.py", "province"),
    ("clean_mtb.py", "province"),
    ("clean_stroller.py", "province"),
    ("clean_via_ferrata.py", "trails, mtb, foot_routes"),
    ("clean_ways.py", "trails, mtb, foot_routes, via_ferrata"),
    ("clean_huts_landmarks.py", "municipalities"),
    ("clean_accommodations.py", "municipalities"),
    ("clean_amenities.py", "huts, accommodations"),
    ("clean_lakes.py", "municipalities"),
    ("clean_mixed_pois.py", "huts, landmarks, food_drink, accommodations, pending files, routes"),
    ("clean_public_transport.py", "_pending_bus_shelters, ways"),
    ("dedup_cross_files.py", "all the point files (rewrites them)"),
]

# entity files: their ids must be unique across files (pending/unmatched files are excluded)
ENTITY_FILES = {
    "trails": "osm_id", "mtb": "osm_id", "foot_routes": "osm_id", "via_ferrata": "id", "ways": "osm_id",
    "municipalities": "osm_id", "huts": "osm_id", "landmarks": "osm_id", "accommodations": "osm_id",
    "food_drink": "osm_id", "lakes": "osm_id", "glaciers": "osm_id", "water_points": "osm_id",
    "cultural_landmarks": "osm_id", "guideposts": "osm_id", "tourist_info": "osm_id", "rest_areas": "osm_id",
    "transport_stops": "osm_id", "aerialways": "osm_id",
}
ROUTES = ("trails", "mtb", "foot_routes", "via_ferrata")


def run_steps():
    for script, needs in STEPS:
        t0 = time.time()
        r = subprocess.run([sys.executable, script], cwd=HERE, capture_output=True, text=True)
        status = "ok" if r.returncode == 0 else "FAILED"
        print(f"[{status}] {script:30} ({time.time() - t0:5.1f} s)  needs: {needs}")
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-4000:])
            sys.exit(1)


def load(name):
    return json.load(open(CLEAN / f"{name}.json", encoding="utf-8"))


def check():
    errors = []
    data = {f: load(f) for f in ENTITY_FILES}
    province = json.load(open(CLEAN / "province.json", encoding="utf-8"))

    # ids: unique in each file (error). The same id in two files is the SAME OSM object with two roles
    # (e.g. a lift that is also a route segment): it becomes one KG entity with two types -> reported, not an error
    owner, shared = {}, []
    for f, key in ENTITY_FILES.items():
        ids = [r[key] for r in data[f]]
        if len(ids) != len(set(ids)):
            errors.append(f"{f}: duplicate ids inside the file")
        for i in ids:
            if i in owner:
                shared.append((i, owner[i], f))
            owner[i] = f
        bad = [i for i in ids if not (i.startswith(("node/", "way/", "relation/", "via_ferrata/")))]
        if bad:
            errors.append(f"{f}: {len(bad)} ids not in the uniform format, e.g. {bad[:3]}")

    # referential integrity
    way_ids = {w["osm_id"] for w in data["ways"]}
    for f in ROUTES:
        miss = {w for r in data[f] for w in r["main_way_ids"]} - way_ids
        if miss:
            errors.append(f"{f}: {len(miss)} main_way_ids not in ways.json")
    istat = {m["istat"] for m in data["municipalities"]}
    for f, rows in data.items():
        for r in rows:
            codes = r.get("municipalities_istat") or ([r["municipality_istat"]] if r.get("municipality_istat") else [])
            if any(c not in istat for c in codes):
                errors.append(f"{f}: {r.get('osm_id', r.get('id'))} has an unknown municipality code")
                break
    muni_osm = {m["osm_id"] for m in data["municipalities"]}
    if set(province["municipality_osm_ids"]) != muni_osm:
        errors.append("province.municipality_osm_ids differ from municipalities.json")
    posts = {g["osm_id"] for g in data["guideposts"]}
    refs = {g for f in ("trails", "mtb", "foot_routes") for r in data[f] for g in r["guidepost_node_ids"]}
    on_route = sum(1 for g in data["guideposts"] if g["on_kept_route"])
    if on_route != len(refs & posts):
        errors.append("guideposts.on_kept_route inconsistent with the routes")

    # summary
    print("\n=== data/clean summary ===")
    total = 0
    for f in ENTITY_FILES:
        n = len(data[f])
        total += n
        dup = sum(1 for r in data[f] if r.get("duplicates"))
        extra = f"  (absorbed duplicates: {dup})" if dup else ""
        print(f"  {f:20} {n:7}{extra}")
    print(f"  {'TOTAL entities':20} {total:7}")
    print(f"  guidepost references of routes found in guideposts.json: {len(refs & posts)} of {len(refs)}")
    print(f"\nsame OSM object in two files (one KG entity with two roles): {len(shared)}",
          dict(Counter(f"{a}+{b}" for _, a, b in shared)))
    for i, a, b in shared:
        print(f"    {i}: {a} + {b}")
    json.dump([{"osm_id": i, "files": [a, b]} for i, a, b in shared],
              open(CLEAN / "_shared_objects.json", "w", encoding="utf-8"), indent=1)
    return errors


def hashes():
    out = {}
    for p in sorted(CLEAN.glob("*.json")) + sorted(CLEAN.glob("*.geojson")):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    return out


if __name__ == "__main__":
    t0 = time.time()
    run_steps()
    errs = check()
    h = hashes()
    json.dump(h, open(HERE / "last_run_hashes.json", "w"), indent=1)
    print(f"\noutput files: {len(h)} (hashes in cleaning/last_run_hashes.json)")
    print(f"total time: {time.time() - t0:.0f} s")
    if errs:
        print("\nCHECKS FAILED:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("\nall checks passed")
