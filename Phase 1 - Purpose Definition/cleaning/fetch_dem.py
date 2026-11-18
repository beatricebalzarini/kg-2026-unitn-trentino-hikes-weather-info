"""Download the Copernicus DEM GLO-30 tiles that cover all the entities (once; skipped if already present).

Source: Copernicus DEM GLO-30 (30 m), public AWS bucket `copernicus-dem-30m`, no registration.
Licence/attribution: "Copernicus DEM © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018,
provided under COPERNICUS by the European Union and ESA; all rights reserved" (free use with attribution).
Output: data/dem/Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM.tif (1°x1° tiles, EPSG:4326)
data/dem/ is in .gitignore: it is large and can be downloaded again at any time.
"""
import json
import math
import sys
import urllib.request
from pathlib import Path

from shapely.geometry import shape

HERE = Path(__file__).resolve().parent
ENT = HERE.parent / "data" / "entities"
DEM = HERE.parent / "data" / "dem"
URL = "https://copernicus-dem-30m.s3.amazonaws.com/{n}/{n}.tif"


def tile_name(lat, lon):
    return f"Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM"


def needed_tiles():
    xs, ys = [], []
    for f in ("routes_geometry.geojson", "landmarks_geometry.geojson"):
        for ft in json.load(open(ENT / f, encoding="utf-8"))["features"]:
            b = shape(ft["geometry"]).bounds
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
    for f in ("hospitality", "facilities", "transport", "landmarks", "municipalities"):
        for r in json.load(open(ENT / f"{f}.json", encoding="utf-8")):
            xs.append(r["lon"])
            ys.append(r["lat"])
    return [(la, lo) for la in range(math.floor(min(ys)), math.floor(max(ys)) + 1)
            for lo in range(math.floor(min(xs)), math.floor(max(xs)) + 1)]


def tile_paths():
    return [DEM / f"{tile_name(la, lo)}.tif" for la, lo in needed_tiles()]


if __name__ == "__main__":
    DEM.mkdir(parents=True, exist_ok=True)
    for la, lo in needed_tiles():
        n = tile_name(la, lo)
        p = DEM / f"{n}.tif"
        if p.exists() and p.stat().st_size > 0:
            print(f"present  {p.name} ({p.stat().st_size / 1e6:.0f} MB)")
            continue
        print(f"download {n} ...", end=" ", flush=True)
        try:
            urllib.request.urlretrieve(URL.format(n=n), p)
        except Exception as e:  # a tile can be missing (e.g. sea only): the caller must handle gaps
            print("FAILED:", e)
            p.unlink(missing_ok=True)
            sys.exit(1)
        print(f"{p.stat().st_size / 1e6:.0f} MB")
