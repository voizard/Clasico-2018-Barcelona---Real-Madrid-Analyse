#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Match context — what actually happened in the game (StatsBomb).

The structural findings (pass networks, pressing height) do not explain
themselves; the match narrative does. This script pulls the facts that frame
them: goals, cards, substitutions, injury stoppages, and a half-by-half split
of possession, shots, xG and crosses.

Why the split matters: a team that plays a man down for a whole half will
naturally concede possession and territory. Without that context, "the opponent
pressed higher" can be misread as a tactical choice when it is really a
numerical one.

Usage:
    python3 src/match_context.py --match 9924
    python3 src/match_context.py --match 9924 --json
"""
from __future__ import annotations

import argparse
import collections
import json
import os

from paths import DATA, EVENTS, event_files, match_id
from short_names import short_name


def collect(path):
    with open(path, encoding="utf-8") as fh:
        ev = json.load(fh)

    out = {"goals": [], "cards": [], "subs": [], "injuries": [],
           "fouls": collections.Counter(), "halves": {}}

    running = collections.Counter()
    for e in ev:
        t = e["type"]["name"]
        minute = e.get("minute", 0)
        team = e["team"]["name"]
        player = (e.get("player") or {}).get("name")

        if t == "Shot" and (e.get("shot") or {}).get("outcome", {}).get("name") == "Goal":
            running[team] += 1
            out["goals"].append({
                "minute": minute, "team": team, "player": player,
                "xg": round(float((e.get("shot") or {}).get("statsbomb_xg") or 0), 2),
                "score": f"{running['Barcelona']}:{running['Real Madrid']}",
            })
        if t == "Own Goal For":
            running[team] += 1

        card = (e.get("foul_committed") or {}).get("card", {}).get("name")
        if card:
            out["cards"].append({"minute": minute, "team": team,
                                 "player": player, "card": card})
        bb = (e.get("bad_behaviour") or {}).get("card", {}).get("name")
        if bb:
            out["cards"].append({"minute": minute, "team": team,
                                 "player": player, "card": bb + " (bad behaviour)"})

        if t == "Substitution":
            rep = (e.get("substitution") or {}).get("replacement") or {}
            out["subs"].append({"minute": minute, "team": team,
                                "off": player, "on": rep.get("name")})
        if t == "Injury Stoppage":
            out["injuries"].append({"minute": minute, "team": team})
        if t == "Foul Committed":
            out["fouls"][team] += 1

    # Half-by-half split. StatsBomb periods: 1 = first half, 2 = second half.
    for label, period in (("first", 1), ("second", 2)):
        sub = [e for e in ev if e.get("period") == period]
        crosses = collections.Counter()
        shots = collections.Counter()
        xg = collections.Counter()
        poss = collections.Counter()
        for e in sub:
            team = e["team"]["name"]
            poss[team] += 1
            if e["type"]["name"] == "Pass" and (e.get("pass") or {}).get("cross"):
                crosses[team] += 1
            if e["type"]["name"] == "Shot":
                shots[team] += 1
                xg[team] += float((e.get("shot") or {}).get("statsbomb_xg") or 0)
        total = sum(poss.values()) or 1
        out["halves"][label] = {
            "possession_pct": {k: round(v / total * 100) for k, v in poss.items()},
            "crosses": dict(crosses), "shots": dict(shots),
            "xg": {k: round(v, 2) for k, v in xg.items()},
        }
    return out


def report(ctx, tag):
    print(f"=== Match context — {tag} ===\n")
    print("Goals (chronological):")
    for g in ctx["goals"]:
        print(f"  {g['minute']:3}'  {g['score']:>3}  {short_name(g['player'])} "
              f"({g['team']})   xG {g['xg']:.2f}")

    print("\nCards:")
    for c in sorted(ctx["cards"], key=lambda x: x["minute"]):
        print(f"  {c['minute']:3}'  {c['card']:24} {short_name(c['player'])} "
              f"({c['team']})")

    print("\nSubstitutions:")
    for s in sorted(ctx["subs"], key=lambda x: x["minute"]):
        print(f"  {s['minute']:3}'  {s['team']:13} off: {short_name(s['off']):18} "
              f"on: {short_name(s['on'])}")

    print("\nInjury stoppages:")
    for i in ctx["injuries"]:
        print(f"  {i['minute']:3}'  {i['team']}")

    print("\nFouls committed:")
    for t, n in ctx["fouls"].most_common():
        print(f"  {t}: {n}")

    print("\nHalf-by-half split:")
    for label in ("first", "second"):
        h = ctx["halves"][label]
        print(f"  {label:6}  possession {h['possession_pct']}  "
              f"crosses {h['crosses']}  shots {h['shots']}  xG {h['xg']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", required=True)
    ap.add_argument("--json", action="store_true", help="also write data/match_context_<id>.json")
    args = ap.parse_args()

    files = [f for f in event_files() if match_id(f) == args.match]
    if not files:
        raise SystemExit(f"match {args.match} not found in {EVENTS}")

    ctx = collect(files[0])
    report(ctx, args.match)

    if args.json:
        os.makedirs(DATA, exist_ok=True)
        ctx["fouls"] = dict(ctx["fouls"])
        path = os.path.join(DATA, f"match_context_{args.match}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(ctx, fh, indent=2, ensure_ascii=False)
        print(f"\nJSON: {path}")


if __name__ == "__main__":
    main()
