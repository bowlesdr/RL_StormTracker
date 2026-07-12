#!/usr/bin/env python3
"""Fetch active forest fires and satellite-derived burned-area perimeters
within Ontario and Quebec from the Canadian Wildland Fire Information System
(CWFIS), and write a simplified forestfires.json into the repo root. Run on
a schedule by .github/workflows/update-forestfires.yml; index.html fetches
the committed JSON directly (same-origin) rather than calling CWFIS from the
browser — the active-fires WFS (on a different host than the rest of CWFIS)
doesn't send CORS headers, so a direct fetch() from a static page can't be
counted on. The perimeters WFS does send them, but it's fetched here too so
both layers come from a single, consistently-cached source.
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Matches ONTARIO_BOUNDS in index.html. Quebec's is this script's own —
# nothing elsewhere in the app currently needs a Quebec bounding box.
ONTARIO_BOUNDS = {"minLat": 41.5, "maxLat": 57, "minLng": -95.5, "maxLng": -74}
QUEBEC_BOUNDS = {"minLat": 44.9, "maxLat": 62.6, "minLng": -79.8, "maxLng": -57.1}
REGIONS = [ONTARIO_BOUNDS, QUEBEC_BOUNDS]

# Smallest rectangle covering both regions — used for the single perimeters
# bbox query below. Looser than checking each province individually (the two
# provinces aren't actually contiguous rectangles), but that's an acceptable
# tradeoff for one query instead of two; the active-fires list below is
# filtered per-region instead, since it's cheap to do client-side.
COMBINED_BOUNDS = {
    "minLat": min(r["minLat"] for r in REGIONS), "maxLat": max(r["maxLat"] for r in REGIONS),
    "minLng": min(r["minLng"] for r in REGIONS), "maxLng": max(r["maxLng"] for r in REGIONS),
}

OUTPUT_PATH = "forestfires.json"

# Agency-reported active fires (name/ID, size, stage of control) — served
# from a separate CWFIS host than the WMS/WFS layers below, undocumented
# publicly; found via `adb`-free digging through CWFIS's own "how to access
# data services" PDF. Filtered here (not via CQL_FILTER) to only fires whose
# validity window covers right now, matching CWFIS's own documented example
# query — this is what keeps long-closed fires from lingering in the feed.
ACTIVEFIRES_URL = "https://geoserver.cwfif.nrcan.gc.ca/geoserver/wfs"
ACTIVEFIRES_PARAMS = {
    "service": "WFS", "version": "2.0.1", "request": "GetFeature",
    "outputFormat": "application/json", "typeName": "public:cwfif_national_activefires",
    "CQL_FILTER": "now()>=record_start AND now()<=record_end",
}

# Satellite hotspot-derived burned-area polygons — bbox-filtered server-side
# (unlike active fires above) since this is a much larger national dataset;
# reprojected to EPSG:4326 on the fly via srsName so no client-side CRS
# handling is needed (the layer's native CRS is EPSG:3978, Canada Atlas
# Lambert).
M3_POLYGONS_URL = "https://cwfis.cfs.nrcan.gc.ca/geoserver/public/wfs"
M3_POLYGONS_PARAMS = {
    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
    "outputFormat": "application/json", "typeName": "public:m3_polygons_current",
    "srsName": "EPSG:4326",
    "CQL_FILTER": (
        f"BBOX(geometry,{COMBINED_BOUNDS['minLng']},{COMBINED_BOUNDS['minLat']},"
        f"{COMBINED_BOUNDS['maxLng']},{COMBINED_BOUNDS['maxLat']})"
    ),
}


def fetch_json(url, params):
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{qs}", timeout=30) as resp:
        return json.load(resp)


def in_scope(lat, lon):
    return any(r["minLat"] <= lat <= r["maxLat"] and r["minLng"] <= lon <= r["maxLng"] for r in REGIONS)


def fetch_fires():
    """Active fires, filtered to Ontario/Quebec client-side (rather than via
    CQL_FILTER) since the feed already includes plain lat/lon properties
    per feature and the whole national dataset is only ~a few hundred rows
    — not worth the extra query complexity."""
    data = fetch_json(ACTIVEFIRES_URL, ACTIVEFIRES_PARAMS)
    fires = []
    for feature in data.get("features", []):
        p = feature["properties"]
        lat, lon = p.get("latitude"), p.get("longitude")
        if lat is None or lon is None or not in_scope(lat, lon):
            continue
        fires.append({
            "id": p.get("national_fire_id"),
            "agency": p.get("agency_code"),
            "region": p.get("region_code"),
            "size_ha": p.get("fire_size"),
            "stage": p.get("stage_of_control_status"),
            "response_type": p.get("response_type"),
            "situation_report_date": p.get("situation_report_date"),
            "status_date": p.get("status_date"),
            "lat": lat,
            "lon": lon,
        })
    return fires


def fetch_perimeters():
    data = fetch_json(M3_POLYGONS_URL, M3_POLYGONS_PARAMS)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": f["geometry"],
                "properties": {
                    "area_ha": f["properties"].get("area"),
                    "hotspot_count": f["properties"].get("hcount"),
                    "first_detected": f["properties"].get("firstdate"),
                    "last_detected": f["properties"].get("lastdate"),
                },
            }
            for f in data.get("features", [])
        ],
    }


def main():
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fires": fetch_fires(),
        "perimeters": fetch_perimeters(),
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(output['fires'])} fires, "
          f"{len(output['perimeters']['features'])} perimeters")


if __name__ == "__main__":
    main()
