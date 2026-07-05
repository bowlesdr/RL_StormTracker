# Rock Lake Weather (RL_StormTracker)

Live: https://bowlesdr.github.io/RL_StormTracker/

A storm-tracking map centered on Rock Lake, ON: animated radar (2h history +
1h forecast), satellite clouds, storm intensity, live lightning strikes with
thunder sound-wave rings, wind stations, severe weather alerts, an
Environment Canada forecast, a historical tornado track, and the Rock Lake
property boundary.

Built on [Leaflet](https://leafletjs.com/) with Esri World Imagery
(satellite) as the base map — no API key required for any of it.

`index.html` is still the whole app — the one exception is the Environment
Canada forecast widget, which reads from a `weather.json` file kept up to
date by a scheduled GitHub Action (see below), since EC's API doesn't
reliably send CORS headers for a static page to call it directly.

## Watching a different location

Add `?coords=lat,lng` to the URL to point the app at a different location
instead of Rock Lake, e.g.:

```
https://bowlesdr.github.io/RL_StormTracker/index.html?coords=44.4736,-77.7579
```

Radar, wind, alerts, and the map center all follow the override. The
Tornado(s), Wind, and Property Boundary options (all specific to the Rock
Lake area) are hidden from the settings panel whenever an override is active.
The Environment Canada forecast widget does **not** follow the override —
it's always Rock Lake's forecast, since `weather.json` is generated for a
single fixed location (see below).

## Environment Canada forecast

`fetch_weather.py` pulls current conditions + forecast for Rock Lake (via
the [`env_canada`](https://pypi.org/project/env_canada/) package) and writes
`weather.json` into the repo root. `.github/workflows/update-weather.yml`
runs that script hourly and commits the result if it changed.

`index.html` fetches `weather.json` same-origin on load — no API key or
backend needed, and no CORS problem since it's just a static file in the
same repo. The widget hides itself if that file goes missing or more than 6
hours stale (i.e. the workflow is broken, not just between runs).

To refresh it locally:

```
pip install env_canada
python fetch_weather.py
```

## Local testing

Double-click `serve.bat`, or run:

```
python -m http.server 8000
```

Then open http://localhost:8000/ in a browser. (Opening `index.html` directly
via double-click won't work — the service worker requires a secure context,
which `file://` doesn't provide; `localhost` counts as secure.)
