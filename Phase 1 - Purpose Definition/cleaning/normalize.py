"""Shared normalization rules, used by every cleaning script (one place for each rule)."""
import math
import re

# ---------------- distances ----------------

def haversine_m(a, b):
    """Geodesic distance in metres between two (lon, lat) points."""
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def line_length_m(coords):
    """Length in metres of a sequence of (lon, lat) points (or a shapely line)."""
    c = list(getattr(coords, "coords", coords))
    return sum(haversine_m(c[i], c[i + 1]) for i in range(len(c) - 1))


# ---------------- operators ----------------
# canonical names for the operators written in many ways in OSM
OPERATOR_RULES = [
    (lambda low: "alpinisti tridentini" in low or re.search(r"(^|\W)s\.?a\.?t\.?(\W|$)", low), "SAT"),
    (lambda low: low.startswith(("club alpino italiano", "cai", "c.a.i.")), "CAI"),
    (lambda low: "alpenverein" in low or low.startswith("avs"), "AVS"),
    (lambda low: "paneveggio" in low or "panevaggio" in low, "Parco Naturale Paneveggio - Pale di San Martino"),
    (lambda low: "riserve alpi ledrensi" in low, "Rete di Riserve Alpi Ledrensi"),
    (lambda low: low.startswith("comune di limone"), "Comune di Limone sul Garda"),
    (lambda low: "trentino trasporti" in low or "ttesercizio" in low, "Trentino Trasporti"),
    (lambda low: "dolomitibus" in low, "DolomitiBus"),
    (lambda low: "rete ferroviaria italiana" in low or low == "rfi", "RFI"),
    (lambda low: low in ("private", "privato", "privat"), "private"),
]


def _canonical(p):
    """-> (canonical name or None if the value must be dropped, True if it matched a known rule)"""
    low = p.lower()
    if re.fullmatch(r"[\d\s.,]+", p):            # coordinates written as operator
        return None, True
    for test, name in OPERATOR_RULES:
        if test(low):
            return name, True
    if low.startswith("linea "):                  # only a bus line ("Linea 101"), not an operator
        return None, True
    if low.startswith("comune di"):
        return "C" + p[1:], True
    return p, False


def norm_operator(op):
    """Operator tag -> list of canonical operators (or None).
    ';' always separates operators. ',' separates them only when at least one part is a known operator
    (e.g. "Comune di Cinte, Comune di Grigno", "Dolomitibus, Trentino Trasporti", "Trentino Trasporti,
    Monauni Carlo") and no part contains digits; not inside a name such as "APT Trento, Monte Bondone,
    Valle dei Laghi", nor in an address ("Hotel Riviera in Viale Rovereto, 95")."""
    if not op:
        return None
    parts = []
    for chunk in op.split(";"):
        sub = [s.strip() for s in chunk.split(",") if s.strip()]
        # (no part with digits: a comma followed by a house number is an address, not a list)
        if len(sub) > 1 and any(_canonical(s)[1] for s in sub) and not any(re.search(r"\d", s) for s in sub):
            parts += sub
        else:
            parts.append(chunk.strip())
    out = []
    for p in parts:
        if not p:
            continue
        c, _ = _canonical(p)
        if c and c not in out:
            out.append(c)
    return out or None
