#!/usr/bin/env python3
"""Fetch the current Environment Canada conditions/forecast for Rock Lake and
write a simplified weather.json into the repo root. Run on a schedule by
.github/workflows/update-weather.yml; index.html fetches the committed JSON
directly (same-origin) rather than calling Environment Canada's API from the
browser, since it doesn't reliably send CORS headers for direct fetch() calls.
"""

import asyncio
import json
from datetime import datetime, timezone

from env_canada import ECWeather

# Matches HOME in index.html.
LAT = 44.80996960818295
LON = -76.25362035830996

OUTPUT_PATH = "weather.json"
DAILY_FORECAST_COUNT = 10


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

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "location": weather.metadata.location,
        "station": weather.metadata.station,
        "current": current,
        "daily": daily,
    }


def main():
    data = asyncio.run(fetch())
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
