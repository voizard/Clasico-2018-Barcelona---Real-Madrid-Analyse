#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crosses (StatsBomb).

A cross is a pass with pass.cross == True. Verified against the raw data: the
Clasico 9924 has 25 such passes out of 1161, so the field is populated, not
guessed.

"Successful" in the narrow sense = completed (no pass.outcome). In the Clasico:
8 of 25. The script also reports whether a cross directly led to a shot
(pass.assisted_shot_id) and whether that shot was a goal.

Map: arrow from cross origin to target.
    green = completed, grey = not completed
Reading direction is made explicit (own goal left, attack to the right).

Usage:
    python3 src/crosses.py                    # all downloaded matches, summary
    python3 src/crosses.py --match 9924       # one match, with per-team maps
    python3 src/crosses.py --match 9924 --completed-only
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from clean_events import load_match
from paths import EVENTS, FIGURES, event_files, match_id
from pitch import draw_pitch, direction_hint
from short_names import short_name

OUT_DIR = FIGURES


def crosses_for_file(path):
    """Crosses of one match as a list of dicts."""
    with open(path, encoding="utf-8") as fh:
        ev = json.load(fh)
    df = load_match(path)
    shot_outcome = {e["id"]: (e.get("shot") or {}).get("outcome", {}).get("name")
                    for e in ev if e["type"]["name"] == "Shot"}
    has_sid = "pass.assisted_shot_id" in df.columns

    sel = ((df["type_name"] == "Pass") & (df["pass.cross"] == True)  # noqa: E712
           & df["loc_x"].notna() & df["pass_end_x"].notna())
    rows = []
    for _, r in df[sel].iterrows():
        completed = not isinstance(r.get("pass.outcome.name"), str)
        sid = r.get("pass.assisted_shot_id") if has_sid else None
        led_to_shot = isinstance(sid, str)
        rows.append({
            "player": r["player_name"], "team": r["team_name"],
            "minute": r["minute"], "x": r["loc_x"], "y": r["loc_y"],
            "end_x": r["pass_end_x"], "end_y": r["pass_end_y"],
            "completed": bool(completed),
            "recipient": r.get("pass.recipient.name"),
            "led_to_shot": bool(led_to_shot),
            "goal": bool(led_to_shot and shot_outcome.get(sid) == "Goal"),
        })
    return rows


def map_for_team(rows, team, tag, out_path):
    sub = [r for r in rows if r["team"] == team]
    fig, ax = plt.subplots(figsize=(10.2, 7))
    for r in sub:
        colour = "#27ae60" if r["completed"] else "#95a5a6"
        ax.annotate("", xy=(r["end_x"], r["end_y"]), xytext=(r["x"], r["y"]),
                    arrowprops=dict(arrowstyle="-|>", color=colour,
                                    lw=2.2 if r["completed"] else 1.1,
                                    alpha=0.95 if r["completed"] else 0.45,
                                    shrinkA=0, shrinkB=0), zorder=3)
        ax.scatter(r["x"], r["y"], s=30, color="#1f4e79", zorder=5,
                   edgecolors="white", linewidths=0.6)
        label = f"{short_name(r['player'])} {int(r['minute'])}'"
        if r["goal"]:
            label += " GOAL"
        ax.annotate(label, xy=(r["x"], r["y"]), xytext=(5, 6),
                    textcoords="offset points", fontsize=6.8,
                    fontweight="bold" if r["goal"] else "normal",
                    color="#000000" if r["goal"] else "#222222", zorder=6)
    draw_pitch(ax)
    direction_hint(ax)
    ok = sum(1 for r in sub if r["completed"])
    goals = sum(1 for r in sub if r["goal"])
    ax.set_title(f"Crosses — {team} ({tag})   {len(sub)} crosses, {ok} completed"
                 + (f", {goals} goal(s)" if goals else "")
                 + "\ndot = cross origin, arrow head = target   |   "
                   "green = completed, grey = not", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def write_csv(rows, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write("player;team;match_id;minute;from_x;from_y;to_x;to_y;"
                 "completed;recipient;led_to_shot;goal\n")

        def z(v):
            return "" if v is None else f"{v:.2f}".replace(".", ",")

        for r in sorted(rows, key=lambda x: (x["team"], x["minute"])):
            fh.write(";".join([
                str(r["player"]), str(r["team"]), str(r["match_id"]),
                str(r["minute"]), z(r["x"]), z(r["y"]), z(r["end_x"]), z(r["end_y"]),
                "yes" if r["completed"] else "no", str(r["recipient"] or ""),
                "yes" if r["led_to_shot"] else "no",
                "yes" if r["goal"] else "no",
            ]) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", help="single match id (e.g. 9924); default all")
    ap.add_argument("--completed-only", action="store_true")
    args = ap.parse_args()

    files = event_files()
    if args.match:
        files = [f for f in files if match_id(f) == args.match]
        if not files:
            raise SystemExit(f"match {args.match} not found in {EVENTS}")
    if not files:
        raise SystemExit("No event files. Run: python3 data/get_data.py")

    all_rows = []
    for f in files:
        for r in crosses_for_file(f):
            r["match_id"] = match_id(f)
            all_rows.append(r)
    if args.completed_only:
        all_rows = [r for r in all_rows if r["completed"]]

    ok = sum(1 for r in all_rows if r["completed"])
    shots = sum(1 for r in all_rows if r["led_to_shot"])
    goals = sum(1 for r in all_rows if r["goal"])
    print(f"matches: {len(files)} | crosses: {len(all_rows)} | completed: {ok} "
          f"| led to shot: {shots} | goals: {goals}")

    agg = {}
    for r in all_rows:
        a = agg.setdefault((r["player"], r["team"]),
                           {"n": 0, "ok": 0, "shot": 0, "goal": 0})
        a["n"] += 1
        a["ok"] += int(r["completed"])
        a["shot"] += int(r["led_to_shot"])
        a["goal"] += int(r["goal"])
    print("\n# crosses per player")
    for (p, t), a in sorted(agg.items(), key=lambda kv: (-kv[1]["ok"], -kv[1]["n"]))[:20]:
        print(f"  {short_name(p):24} {t[:16]:16} total {a['n']:3d} | "
              f"completed {a['ok']:3d} | led to shot {a['shot']:2d} | goals {a['goal']}")

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(OUT_DIR), "data"), exist_ok=True)
    tag = args.match or "all_matches"
    if args.match and not args.completed_only:
        for t in sorted({r["team"] for r in all_rows}):
            out = os.path.join(OUT_DIR, f"crosses_{tag}_{t.split()[0]}.png")
            map_for_team(all_rows, t, tag, out)
            print(f"map: {out}")
    csv = os.path.join(os.path.dirname(OUT_DIR), "data", f"crosses_{tag}.csv")
    write_csv(all_rows, csv)
    print(f"\nCSV: {csv}")


if __name__ == "__main__":
    main()
