#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pass network — the most frequent passing connections within a team.

Each player sits at the average position of his ball actions; lines connect the
pairs that passed to each other most often (thickness = count). Player dot size
scales with involvement.

The receiver comes from the field `pass.recipient`, which StatsBomb fills for
most passes (1081 of 1161 in the Clasico) — not guessed. Passes without a
recipient are skipped rather than attributed to a fallback, so the counts are
conservative.

Reading the map: a player's dot position *is* the finding. A defensive
midfielder whose dot sits on the centre-back line played as a third centre-back;
a full-back whose dot sits high and wide held a lot of the ball in advanced
areas.

Usage:
    python3 src/pass_network.py --match 9924
    python3 src/pass_network.py --match 9924 --min-count 8
"""
from __future__ import annotations

import argparse
import collections
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from clean_events import load_match
from paths import DATA, FIGURES, EVENTS, event_files, match_id
from pitch import draw_pitch, direction_hint
from short_names import short_name

OUT_DIR = FIGURES


def pass_pairs(df, team):
    """(sender, receiver) -> count, plus mean position per player."""
    sub = df[(df["type_name"] == "Pass") & (df["team_name"] == team)]
    pairs = collections.Counter()
    for _, r in sub.iterrows():
        rec = r.get("pass.recipient.name")
        if not isinstance(rec, str) or not rec or rec == r["player_name"]:
            continue
        pairs[(r["player_name"], rec)] += 1

    pos = {}
    actions = df[(df["team_name"] == team) & df["loc_x"].notna()]
    for name, grp in actions.groupby("player_name"):
        pos[name] = (grp["loc_x"].mean(), grp["loc_y"].mean())
    return pairs, pos


def draw_network(df, team, out_path, min_count=5, label_top=12):
    pairs, pos = pass_pairs(df, team)
    fig, ax = plt.subplots(figsize=(11, 7.4))

    top = max(pairs.values()) if pairs else 1
    drawn = 0
    for (a, b), n in pairs.most_common():
        if n < min_count or a not in pos or b not in pos:
            continue
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ax.plot([x1, x2], [y1, y2], color="#c0392b",
                lw=0.4 + 3.2 * (n / top), alpha=0.55, zorder=3,
                solid_capstyle="round")
        drawn += 1

    touches = (df[(df["team_name"] == team) & df["loc_x"].notna()]
               .groupby("player_name").size())
    labelled = list(touches.sort_values(ascending=False).head(label_top).index)

    # Dots first, then labels with collision avoidance: two players standing close
    # (Benzema / Asensio) would otherwise print on top of each other.
    for name, (x, y) in pos.items():
        big = name in labelled
        ax.scatter([x], [y], s=(70 + 1.1 * touches.get(name, 0)) if big else 45,
                   color="#10375c" if big else "#7f8c8d",
                   edgecolor="white", linewidth=1.3, zorder=6)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    offsets = [(6, 7), (6, -12), (-6, 7), (-6, -12), (6, 18), (6, -23),
               (-6, 18), (-6, -23)]
    taken = []
    for name in labelled:
        x, y = pos[name]
        ann = ax.annotate(short_name(name), (x, y), xytext=offsets[0],
                          textcoords="offset points", fontsize=8.5,
                          weight="bold", color="#10375c", zorder=7)
        for off in offsets:
            ann.set_position(off)
            bb = ann.get_window_extent(renderer)
            if not any(bb.overlaps(b) for b in taken):
                break
        taken.append(ann.get_window_extent(renderer))

    draw_pitch(ax)
    direction_hint(ax)
    ax.set_title(f"Pass network — {team} ({match_id_of(df)})   "
                 f"dot = mean position, line thickness = passes "
                 f"(shown from {min_count})", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return pairs, pos, drawn


def match_id_of(df):
    return getattr(df, "attrs", {}).get("match_id", "")


def write_csv(pairs, team, mid, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write("match_id;team;from;from_short;to;to_short;count\n")
        for (a, b), n in pairs.most_common():
            fh.write(";".join([mid, team, a, short_name(a), b,
                               short_name(b), str(n)]) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", required=True, help="match id (e.g. 9924)")
    ap.add_argument("--min-count", type=int, default=5,
                    help="only draw connections with at least this many passes")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    files = [f for f in event_files() if match_id(f) == args.match]
    if not files:
        raise SystemExit(f"match {args.match} not found in {EVENTS}")

    df = load_match(files[0])
    df.attrs["match_id"] = args.match
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)

    for team in dict.fromkeys(df["team_name"].dropna()):
        out = os.path.join(OUT_DIR, f"pass_network_{args.match}_{team.split()[0]}.png")
        pairs, pos, drawn = draw_network(df, team, out, args.min_count)
        csv = os.path.join(DATA, f"pass_network_{args.match}_{team.split()[0]}.csv")
        write_csv(pairs, team, args.match, csv)
        print(f"\n{team}: {drawn} lines drawn -> {out}")
        for (a, b), n in pairs.most_common(args.top):
            print(f"  {n:>3}x  {short_name(a):<14} -> {short_name(b)}")


if __name__ == "__main__":
    main()
