# Rock Lake Weather (RL_StormTracker)

Live: https://bowlesdr.github.io/RL_StormTracker/

## Local testing

Double-click `serve.bat`, or run:

```
python -m http.server 8000
```

Then open http://localhost:8000/ in a browser. (Opening `index.html` directly via
double-click won't work — the Maps API key is referrer-restricted to HTTP origins,
and the service worker requires a secure context, neither of which `file://` provides.)

## Google Maps API key restrictions

Configured in Google Cloud Console under the key's **Websites** restriction:

- `https://bowlesdr.github.io/*`
- `http://localhost:8000/*`
