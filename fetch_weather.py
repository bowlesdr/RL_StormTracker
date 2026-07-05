#!/usr/bin/env python3
"""Fetch the current Environment Canada conditions/forecast for Rock Lake and
write a simplified weather.json into the repo root. Run on a schedule by
.github/workflows/update-weather.yml; index.html fetches the committed JSON
directly (same-origin) rather than calling Environment Canada's API from the
browser, since it doesn't reliably send CORS headers for direct fetch() calls.
"""

import asyncio
import io
import json
import urllib.request
from datetime import datetime, timezone

import numpy as np
from PIL import Image

from env_canada import ECWeather

# Matches HOME in index.html.
LAT = 44.80996960818295
LON = -76.25362035830996

OUTPUT_PATH = "weather.json"
DAILY_FORECAST_COUNT = 10

# EC's own citypage feed (above) has no precipitation *amount*, only
# probability — confirmed by inspecting its raw XML directly. This second
# source is MSC GeoMet's WCS, which exposes the Regional Deterministic
# Prediction System's raw hourly precip accumulation as a queryable
# coverage. A tiny bounding-box GetCoverage request returns a handful of
# pixels (a few hundred bytes) rather than the full ~2.3MB continental
# grid. Its "time" dimension is a strict PT1H step starting at a fixed
# hour — verified it rejects both out-of-range and off-the-hour values
# with a real ServiceExceptionReport rather than silently defaulting. EC's
# own hourly periods are already whole UTC hours, so they land on that grid
# exactly — the only wrinkle is it wants a literal "Z" suffix, and rejects
# Python's own +00:00 isoformat() rendering of the same instant.
GEOMET_WCS_URL = "https://geo.weather.gc.ca/geomet"
PRECIP_HOURLY_COVERAGE = "RDPS_10km_Precip-Accum1h"
PRECIP_BBOX_DEG = 0.15  # wide enough to reliably span at least one 10km grid cell


def fetch_precip_mm(time_iso: str) -> float | None:
    """Precip accumulated during the hour ending at time_iso, in mm, from
    RDPS (~10km grid, ~84h horizon) — or None on any failure, since this is
    a secondary enrichment and shouldn't take down the whole fetch."""
    try:
        wcs_time = time_iso.replace("+00:00", "Z")
        qs = (
            f"service=WCS&version=2.0.1&request=GetCoverage"
            f"&coverageId={PRECIP_HOURLY_COVERAGE}&format=image/tiff&time={wcs_time}"
            f"&subset=Lat({LAT - PRECIP_BBOX_DEG},{LAT + PRECIP_BBOX_DEG})"
            f"&subset=Long({LON - PRECIP_BBOX_DEG},{LON + PRECIP_BBOX_DEG})"
        )
        with urllib.request.urlopen(f"{GEOMET_WCS_URL}?{qs}", timeout=10) as resp:
            data = resp.read()
        arr = np.array(Image.open(io.BytesIO(data)))
        return round(float(arr.mean()), 1)
    except Exception:
        return None


def value_of(entry):
    return entry.get("value") if isinstance(entry, dict) else entry


async def fetch():
    weather = ECWeather(coordinates=(LAT, LON), language="english")
    await weather.update()

    c = weather.conditions
    current = {
        "temperature": value_of(c.get("temperature")),
        "condition": value_of(c.get("condition")),
        "high_temp": value_of(c.get("high_temp")),
        "low_temp": value_of(c.get("low_temp")),
        "humidity": value_of(c.get("humidity")),
        "wind_speed": value_of(c.get("wind_speed")),
        "wind_dir": value_of(c.get("wind_dir")),
        "text_summary": value_of(c.get("text_summary")),
    }

    daily = [
        {
            "period": f.get("period"),
            "text_summary": f.get("text_summary"),
            "temperature": f.get("temperature"),
            "temperature_class": f.get("temperature_class"),
            "precip_probability": f.get("precip_probability"),
        }
        for f in weather.daily_forecasts[:DAILY_FORECAST_COUNT]
    ]

    # EC only provides an hourly breakdown for roughly the next 24h (not per
    # day for the full daily_forecasts range above), so this is exposed as
    # one rolling window rather than attached to individual daily periods.
    hourly = []
    for h in weather.hourly_forecasts:
        period_iso = h.get("period").isoformat() if h.get("period") else None
        hourly.append({
            "period": period_iso,
            "condition": h.get("condition"),
            "temperature": h.get("temperature"),
            "precip_probability": h.get("precip_probability"),
            "precip_mm": fetch_precip_mm(period_iso) if period_iso else None,
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "location": weather.metadata.location,
        "station": weather.metadata.station,
        "current": current,
        "daily": daily,
        "hourly": hourly,
    }


def main():
    data = asyncio.run(fetch())
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
