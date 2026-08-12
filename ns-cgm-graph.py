#!/usr/bin/env python3
"""Generate an SVG graph of recent Nightscout CGM data.

Usage:
    python3 ns-cgm-graph.py [--url http://127.0.0.1:1337] [--hours 24] [--out cgm.svg]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

MGDL_TO_MMOL = 18.0
DEFAULT_HOURS = 24
DEFAULT_OUT = "cgm.svg"


def _env_path() -> str:
    path = os.environ.get("NS_ENV")
    if not path:
        raise RuntimeError("NS_ENV must point to your Nightscout .env file")
    return path


def api_hash() -> str:
    path = _env_path()
    with open(path) as f:
        for line in f:
            if line.startswith("API_SECRET="):
                secret = line.split("=", 1)[1].strip()
                return hashlib.sha1(secret.encode()).hexdigest()
    raise RuntimeError("API_SECRET not found in " + path)


def ns_get(base: str, path: str, params: str = "") -> list[dict]:
    url = f"{base}{path}{params}"
    req = urllib.request.Request(url, headers={"API-SECRET": api_hash()})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} from {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_entries(base: str, hours: int) -> list[dict]:
    since = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)).timestamp() * 1000)
    return ns_get(base, "/api/v1/entries.json", f"?find[date][$gte]={since}&count=10000") or []


def mmol(bg_mgdl: float) -> float:
    return bg_mgdl / MGDL_TO_MMOL


def main() -> int:
    p = argparse.ArgumentParser(description="Nightscout CGM SVG graph")
    p.add_argument("--url", help="Nightscout base URL (default: NS_URL env or http://127.0.0.1:1337)")
    p.add_argument("--hours", type=int, default=DEFAULT_HOURS, help="Lookback window in hours")
    p.add_argument("--out", default=DEFAULT_OUT, help="Output SVG path")
    args = p.parse_args()

    base = (args.url or os.environ.get("NS_URL") or "http://127.0.0.1:1337").rstrip("/")
    entries = fetch_entries(base, args.hours)

    if not entries:
        print("No entries found.")
        return 0

    points = []
    for e in entries:
        if e.get("sgv") is None:
            continue
        ts = dt.datetime.fromtimestamp(e["date"] / 1000, tz=dt.timezone.utc)
        bg = mmol(e["sgv"])
        points.append((ts, bg))

    if not points:
        print("No SGV values found.")
        return 0

    points.sort()
    width, height = 900, 320
    pad = 40
    now = points[-1][0]
    t_min = now - dt.timedelta(hours=args.hours)
    t_max = now
    bg_min = max(1.0, min(bg for _, bg in points) - 1.0)
    bg_max = min(30.0, max(bg for _, bg in points) + 1.0)

    def tx(t: dt.datetime) -> float:
        return pad + (t - t_min).total_seconds() / (t_max - t_min).total_seconds() * (width - 2 * pad)

    def ty(bg: float) -> float:
        return height - pad - (bg - bg_min) / (bg_max - bg_min) * (height - 2 * pad)

    poly = " ".join(f"{tx(t):.1f},{ty(bg):.1f}" for t, bg in points)

    # Range bands
    hypo_top = ty(3.9)
    target_bottom = ty(10.0)
    hyper_bottom = ty(3.9)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#0b0c10"/>
  <rect x="{pad}" y="{target_bottom:.1f}" width="{width - 2*pad}" height="{hypo_top - target_bottom:.1f}" fill="#4ade80" opacity="0.08"/>
  <polyline fill="none" stroke="#d4a64a" stroke-width="2" points="{poly}"/>
  <text x="{pad}" y="20" fill="#9aa0aa" font-family="ui-sans-serif,system-ui" font-size="11">Nightscout CGM — last {args.hours}h</text>
  <text x="{width - pad}" y="20" fill="#9aa0aa" font-family="ui-sans-serif,system-ui" font-size="11" text-anchor="end">avg {mmol(sum(bg for _, bg in points) / len(points)):.1f} mmol/L</text>
</svg>"""

    with open(args.out, "w") as f:
        f.write(svg)

    print(f"Wrote {args.out} ({len(points)} points, {args.hours}h)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
