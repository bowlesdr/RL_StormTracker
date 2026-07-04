# Rock Lake Weather (RL_StormTracker)

Live: https://bowlesdr.github.io/RL_StormTracker/

A single-file storm-tracking map centered on Rock Lake, ON: animated radar
(2h history + 1h forecast), satellite clouds, storm intensity, live lightning
strikes with thunder sound-wave rings, wind stations, severe weather alerts,
a historical tornado track, and the Rock Lake property boundary.

Built on [Leaflet](https://leafletjs.com/) with Esri World Imagery
(satellite) as the base map — no API key required for any of it.

## Watching a different location

Add `?coords=lat,lng` to the URL to point the app at a different location
instead of Rock Lake, e.g.:

```
https://bowlesdr.github.io/RL_StormTracker/index.html?coords=44.4736,-77.7579
```

Radar, wind, alerts, and the map center all follow the override. The
Tornado(s), Wind, and Property Boundary options (all specific to the Rock
Lake area) are hidden from the settings panel whenever an override is active.

## Local testing

Double-click `serve.bat`, or run:

```
python -m http.server 8000
```

Then open http://localhost:8000/ in a browser. (Opening `index.html` directly
via double-click won't work — the service worker requires a secure context,
which `file://` doesn't provide; `localhost` counts as secure.)
