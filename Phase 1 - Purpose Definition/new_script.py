import json
import time

import numpy as np
import pandas as pd
import requests
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union
from pathlib import Path

# ================= PARAMETRI =================
START, END = "2026-10-01", "2026-11-14"
STEP = 0.1                    # passo griglia in gradi (~8-11 km)
BANDS = [800, 1500, 2200]     # fasce di quota (m)
BORDER_BUFFER = 0.05          # gradi: tiene anche le celle appena fuori confine
BATCH = 40                     # punti per richiesta (prova con 40)

# soglie delle regole (documentale nel progetto!)
DRY_MM = 1.0                  # asciutto: meno di 1 mm nei 3 giorni prima e nel giorno
GOOD_PRECIP_MM = 1.0          # bel tempo: meno di 1 mm di pioggia...
GOOD_SUN_RATIO = 0.6          # ...e almeno il 60% delle ore di luce con il sole
SNOW_DEPTH_M = 0.02           # neve presente: almeno 2 cm al suolo (o nevicata)

URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
DATA_SOURCE = "Open-Meteo Historical Forecast API (CC BY 4.0)"
DATA_TYPE = "historical_forecast"

DAILY = ["weather_code", "precipitation_sum", "rain_sum", "snowfall_sum",
         "sunshine_duration", "daylight_duration",
         "temperature_2m_max", "temperature_2m_min"]
HOURLY = ["snow_depth", "freezing_level_height"]

# ================= 1. CONFINE PROVINCIALE =================
def load_province(path):
    data = json.load(open(path, encoding="utf-8"))
    lines = []
    for el in data["elements"]:
        if el["type"] != "relation":
            continue
        for m in el.get("members", []):
            if m["type"] == "way" and m.get("role") in ("outer", "") and "geometry" in m:
                coords = [(p["lon"], p["lat"]) for p in m["geometry"]]
                if len(coords) >= 2:
                    lines.append(LineString(coords))
    polys = list(polygonize(unary_union(lines)))
    if not polys:
        raise RuntimeError("Non sono riuscito a ricostruire il poligono del confine")
    return unary_union(polys)

#province = load_province(glob.glob("confine-provinciale.json")[0])
BASE = Path(__file__).resolve().parent
BORDER_FILE = BASE / "data" / "confine-provinciale.json"

print("Cerco il confine in:", BORDER_FILE)
print("Il file esiste?", BORDER_FILE.exists())

province = load_province(BORDER_FILE)
area = province.buffer(BORDER_BUFFER)
print("Confine caricato, riquadro:", [round(x, 2) for x in province.bounds])

# ================= 2. GRIGLIA DENTRO IL TRENTINO =================
minx, miny, maxx, maxy = area.bounds
points = []
for lat in np.arange(np.floor(miny * 10) / 10, maxy + STEP, STEP):
    for lon in np.arange(np.floor(minx * 10) / 10, maxx + STEP, STEP):
        lat_r, lon_r = round(float(lat), 2), round(float(lon), 2)
        if area.contains(Point(lon_r, lat_r)):
            for elev in BANDS:
                points.append({"lat": lat_r, "lon": lon_r, "elev": elev,
                               "cell_id": f"cell_{lat_r:.2f}_{lon_r:.2f}_{elev}"})
print("Punti da scaricare:", len(points))

# ================= 3. DOWNLOAD =================
# scarico 3 giorni prima di START per calcolare "asciutto" anche nei primi giorni
fetch_start = (pd.Timestamp(START) - pd.Timedelta(days=3)).strftime("%Y-%m-%d")

def fetch(batch):
    params = {
        "latitude":   ",".join(str(p["lat"]) for p in batch),
        "longitude":  ",".join(str(p["lon"]) for p in batch),
        "elevation":  ",".join(str(p["elev"]) for p in batch),
        "start_date": fetch_start, "end_date": END,
        "daily": ",".join(DAILY), "hourly": ",".join(HOURLY),
        "timezone": "Europe/Rome",
    }
    for attempt in range(5):
        r = requests.get(URL, params=params, timeout=120)
        if r.status_code == 200:
            data = r.json()
            return data if isinstance(data, list) else [data]
        if r.status_code == 429:
            time.sleep(60 * (attempt + 1))
            continue
        r.raise_for_status()
    raise RuntimeError("Troppi tentativi falliti")

rows = []
for i in range(0, len(points), BATCH):
    batch = points[i:i + BATCH]
    for p, res in zip(batch, fetch(batch)):
        daily = pd.DataFrame(res["daily"]).rename(columns={"time": "date"})
        hourly = pd.DataFrame(res["hourly"])
        hourly["date"] = hourly["time"].str[:10]
        h = hourly.groupby("date").agg(
            snow_depth_max=("snow_depth", "max"),
            freezing_level_m=("freezing_level_height", "mean"),
        ).reset_index()
        df = daily.merge(h, on="date", how="left")
        df["cell_id"], df["lat"], df["lon"], df["elev_m"] = (
            p["cell_id"], p["lat"], p["lon"], p["elev"])
        rows.append(df)
    print(f"{min(i + BATCH, len(points))}/{len(points)}")
    time.sleep(2)

df = pd.concat(rows, ignore_index=True)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values(["cell_id", "date"])

# ================= 4. REGOLE DERIVATE =================
# precipitazioni dei 3 giorni PRECEDENTI (D-3..D-1)
df["precip_prev3_mm"] = df.groupby("cell_id")["precipitation_sum"].transform(
    lambda s: s.shift(1).rolling(3).sum())
df = df[df["date"] >= START].copy()          # tolgo i 3 giorni extra

df["sunshine_ratio"] = df["sunshine_duration"] / df["daylight_duration"]

df["dry"] = (df["precip_prev3_mm"] < DRY_MM) & (df["precipitation_sum"] < DRY_MM)
df["good_weather"] = ((df["precipitation_sum"] < GOOD_PRECIP_MM)
                      & (df["sunshine_ratio"] >= GOOD_SUN_RATIO))
df["snow"] = ((df["snow_depth_max"].fillna(0) >= SNOW_DEPTH_M)
              | (df["snowfall_sum"].fillna(0) > 0))

nan_snow = df["snow_depth_max"].isna().mean()
if nan_snow > 0:
    print(f"ATTENZIONE: snow_depth mancante nel {nan_snow:.0%} delle righe")

# ================= 5. CSV PER LE TRIPLE =================
df["obs_id"] = df["cell_id"] + "_" + df["date"].dt.strftime("%Y%m%d")
df["date"] = df["date"].dt.strftime("%Y-%m-%d")
df["sunshine_h"] = df["sunshine_duration"] / 3600
df["daylight_h"] = df["daylight_duration"] / 3600
for c in ["dry", "good_weather", "snow"]:
    df[c] = df[c].map({True: "true", False: "false"})
df["data_source"], df["data_type"] = DATA_SOURCE, DATA_TYPE

obs = df.rename(columns={
    "precipitation_sum": "precipitation_mm", "rain_sum": "rain_mm",
    "snowfall_sum": "snowfall_cm", "temperature_2m_max": "temp_max_c",
    "temperature_2m_min": "temp_min_c", "snow_depth_max": "snow_depth_max_m",
})[["obs_id", "cell_id", "date", "weather_code", "precipitation_mm", "rain_mm",
    "snowfall_cm", "sunshine_h", "daylight_h", "sunshine_ratio",
    "temp_max_c", "temp_min_c", "snow_depth_max_m", "freezing_level_m",
    "precip_prev3_mm", "dry", "good_weather", "snow",
    "data_source", "data_type"]].round(3)
obs.to_csv("weather_observations.csv", index=False, encoding="utf-8")

cells = df[["cell_id", "lat", "lon", "elev_m"]].drop_duplicates()
cells["wkt"] = cells.apply(lambda r: f"POINT({r['lon']} {r['lat']})", axis=1)
cells.to_csv("weather_cells.csv", index=False, encoding="utf-8")

print("Osservazioni:", len(obs), "| Celle:", len(cells))