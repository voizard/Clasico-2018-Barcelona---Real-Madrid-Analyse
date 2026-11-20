#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify the StatsBomb match files: teams, home/away, score, shots, xG.

Writes data/matches.json and prints a table. Home/away follows StatsBomb's
convention: the first Starting XI event is the home team.

Usage:
    python3 src/identify_matches.py
"""
from __future__ import annotations

import json
import os

from paths import DATA, event_files, match_id


def goals(ev, team_id):
    n = 0
    for e in ev:
        t = e.get("type", {}).get("name")
        if e.get("team", {}).get("id") != team_id:
            continue
        if t == "Shot" and e.get("shot", {}).get("outcome", {}).get("name") == "Goal":
            n += 1
        # An own goal is credited to the opposing team via "Own Goal For".
        if t == "Own Goal For":
            n += 1
    return n


def shots_xg(ev, team_id):
    shots, xg = 0, 0.0
    for e in ev:
        if e.get("type", {}).get("name") == "Shot" and e.get("team", {}).get("id") == team_id:
            shots += 1
            xg += float(e.get("shot", {}).get("statsbomb_xg") or 0.0)
    return shots, xg


def main():
    files = event_files()
    if not files:
        raise SystemExit("No event files in data/events/. Run: python3 data/get_data.py")
    out = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            ev = json.load(fh)
        xi = [e for e in ev if e.get("type", {}).get("name") == "Starting XI"]
        teams = []
        for e in xi:
            t = e["team"]
            if t["id"] not in [x["id"] for x in teams]:
                teams.append(t)
        home, away = teams[0], teams[1]
        hs, as_ = goals(ev, home["id"]), goals(ev, away["id"])
        hshots, hxg = shots_xg(ev, home["id"])
        ashots, axg = shots_xg(ev, away["id"])
        periods = max(e.get("period", 1) for e in ev)
        out.append(dict(
            match_id=match_id(f), events=len(ev), periods=periods,
            home=home["name"], away=away["name"], score=f"{hs}:{as_}",
            shots=f"{hshots}:{ashots}", xg=f"{hxg:.2f}:{axg:.2f}",
            formations=f"{xi[0].get('tactics', {}).get('formation')}"
                       f" / {xi[1].get('tactics', {}).get('formation')}",
        ))
    out.sort(key=lambda r: r["match_id"])
    print(f"{'match':>6}  {'home':<18} {'away':<18} {'score':>5}  "
          f"{'shots':>7}  {'xG':>11}  P  Ev")
    for r in out:
        print(f"{r['match_id']:>6}  {r['home']:<18} {r['away']:<18} {r['score']:>5}  "
              f"{r['shots']:>7}  {r['xg']:>11}  P{r['periods']}  {r['events']}")
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "matches.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(f"\n{len(out)} matches -> data/matches.json")


if __name__ == "__main__":
    main()
