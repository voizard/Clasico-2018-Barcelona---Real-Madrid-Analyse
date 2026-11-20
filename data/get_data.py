#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download the raw StatsBomb event files used by this project.

The raw match data belongs to StatsBomb and is not redistributed here. It is
published as *StatsBomb Open Data* (https://github.com/statsbomb/open-data)
under their own terms: free to use for non-commercial purposes with attribution
to StatsBomb. Please read that repository's LICENSE before reusing the data.

The files are plain JSON event exports, one per match. This script fetches them
into data/events/, where the analysis scripts expect them.

Usage:
    python3 data/get_data.py            # fetch everything (skips present files)
    python3 data/get_data.py --force    # re-download
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request

BASE = ("https://raw.githubusercontent.com/statsbomb/open-data/"
        "master/data/events/{mid}.json")

# All matches used in the analysis. See the README for what each is.
MATCH_IDS = [
    # La Liga 2017/18 — FC Barcelona (batch A)
    "9754", "9765", "9774", "9783", "9794", "9799",
    # La Liga 2017/18 — FC Barcelona (batch B)
    "9880", "9889", "9912", "9924", "9928", "9948",
    # FIFA World Cup 2018 (batch C)
    "7567", "7568", "7569", "7570",
    # La Liga 2017/18 — FC Barcelona (batch C)
    "9811", "9827", "9837", "9855", "9860", "9870",
]

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "events")


def fetch(mid: str, force: bool = False) -> str:
    target = os.path.join(OUT_DIR, f"{mid}.json")
    if os.path.exists(target) and not force:
        return "already present"
    url = BASE.format(mid=mid)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code} — not available"
    except urllib.error.URLError as exc:
        return f"network error: {exc.reason}"
    with open(target, "wb") as fh:
        fh.write(data)
    return f"{len(data):,} bytes"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Target: {OUT_DIR}")
    problems = 0
    for mid in MATCH_IDS:
        status = fetch(mid, args.force)
        print(f"  {mid}: {status}")
        if status.startswith(("HTTP", "network")):
            problems += 1
    print(f"\n{len(MATCH_IDS) - problems} of {len(MATCH_IDS)} files ready.")
    if problems:
        print("Some files could not be fetched — the analysis for those matches "
              "will be skipped.", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
