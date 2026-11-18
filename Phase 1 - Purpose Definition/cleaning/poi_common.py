"""Helpers shared by the POI cleaning scripts (point datasets)."""
import json
import re

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from route_common import BASE, load_province

CLEAN = BASE / "data" / "clean"


def position(el):
    """lat/lon of a node, or the `center` of a way/relation."""
    if "lat" in el:
        return el["lat"], el["lon"]
    if "center" in el:
        return el["center"]["lat"], el["center"]["lon"]
    return None


def osm_key(el):
    """OSM ids are unique only together with the element type."""
    return f"{el['type']}/{el['id']}"


class Municipalities:
    """Point-in-polygon lookup on data/clean/municipalities_boundaries.geojson."""

    def __init__(self):
        feats = json.load(open(CLEAN / "municipalities_boundaries.geojson", encoding="utf-8"))["features"]
        self.geoms = [shape(f["geometry"]) for f in feats]
        self.props = [f["properties"] for f in feats]
        self.tree = STRtree(self.geoms)
        self.province = load_province()

    def find(self, lat, lon):
        p = Point(lon, lat)
        for i in self.tree.query(p):
            if self.geoms[i].covers(p):
                return self.props[i]
        return None


def to_int(v):
    if v is None:
        return None
    m = re.match(r"\s*(\d+)", v)
    return int(m.group(1)) if m else None


def ele_m(v):
    """Elevation in metres (rounded). Accepts '2069', '2069.5', '2069 m'."""
    if v is None:
        return None
    m = re.match(r"\s*(\d+(?:[.,]\d+)?)", v)
    return round(float(m.group(1).replace(",", "."))) if m else None


def yes_no(v):
    return True if v == "yes" else False if v == "no" else None


def split_values(v):
    return [p.strip() for p in re.split(r"[;,]", v) if p.strip()] if v else []


def phones(t):
    """phone + contact:phone + contact:mobile -> list of '+39...' without spaces, deduplicated."""
    out = []
    for k in ("phone", "contact:phone", "contact:mobile", "mobile"):
        for p in (t.get(k) or "").split(";"):
            p = re.sub(r"[\s\-./()]", "", p)
            if not p:
                continue
            if p.startswith("00"):
                p = "+" + p[2:]
            elif not p.startswith("+"):
                p = "+39" + p
            if p not in out:
                out.append(p)
    return out or None


CUISINE_ALIASES = {"italian_pizza": "pizza"}


def cuisine_list(v):
    """'pizza;Regional, italian_pizza' -> ['pizza', 'regional'] (lowercase, split, aliases, dedup)."""
    out = []
    for c in split_values(v):
        c = CUISINE_ALIASES.get(c.lower().replace(" ", "_"), c.lower().replace(" ", "_"))
        if c not in out:
            out.append(c)
    return out or None


def first_of(t, *keys):
    for k in keys:
        if t.get(k):
            return t[k].strip()
    return None


def norm_operator(op):
    """SAT / CAI / AVS spellings and sections merged; 'privato' -> 'private'; coordinates dropped."""
    if not op:
        return None
    out = []
    for p in (x.strip() for x in op.split(";")):
        low = p.lower()
        if not p or re.fullmatch(r"[\d\s.,]+", p):          # e.g. "46,2538547, 10,8922097"
            continue
        if "alpinisti tridentini" in low or re.search(r"(^|\W)s\.?a\.?t\.?(\W|$)", low):
            p = "SAT"
        elif low.startswith(("club alpino italiano", "cai", "c.a.i.")):
            p = "CAI"
        elif "alpenverein" in low or low.startswith("avs"):
            p = "AVS"
        elif low in ("private", "privato", "privat"):
            p = "private"
        if p not in out:
            out.append(p)
    return out or None
