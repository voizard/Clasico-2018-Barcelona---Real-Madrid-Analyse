#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ball recoveries as coloured dots per player (StatsBomb).

NOT a heatmap — every recovery is a single dot, coloured by player.

What counts as a recovery (verified against the raw data, Clasico 9924):
  * Ball Recovery — player wins the ball back.
        74 events, 5 of them flagged 'recovery_failure' -> 69 genuine.
        Failed ones are dropped by default (--with-failures includes them).
  * Interception — player cuts out a pass.
        20 events. Only the won ones count: 'Won' (11) and
        'Success In Play' (3) = 14. 'Lost Out' (4) and 'Lost In Play' (2) are
        NOT recoveries. --all-interceptions includes the lost ones.

Default: 69 + 14 = 83 recoveries in the Clasico.

Options:
  --only-shots   only recoveries followed, in the same possession, by a shot of
                 the same team. Such a recovery is labelled with its minute, and
                 a gold ring marks the one that ended in a goal.
  --by-zone      longitudinal distribution per team (was this team pressing
                 high?) as a two-panel histogram, with goalkeeper recoveries
                 highlighted, because they skew the mean.

Usage:
    python3 src/recoveries.py --match 9924
    python3 src/recoveries.py --match 9924 --only-shots
    python3 src/recoveries.py --match 9924 --by-zone
    python3 src/recoveries.py                    # all matches, summary only
"""
from __future__ import annotations

import argparse
import collections
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from clean_events import load_match
from paths import DATA, FIGURES, EVENTS, event_files, match_id
from pitch import draw_pitch, direction_hint
from short_names import short_name

OUT_DIR = FIGURES
INTERCEPTION_OK = ("Won", "Success In Play")

# Fixed, well-separated palette (tab20) so the same colour means the same player
# in every figure.
PALETTE = list(plt.get_cmap("tab20").colors) + list(plt.get_cmap("tab20b").colors)


def recoveries(df, with_failures=False, all_interceptions=False):
    """DataFrame of ball recoveries (with a coordinate)."""
    br = df["type_name"] == "Ball Recovery"
    if not with_failures:
        br &= df["ball_recovery.recovery_failure"] != True  # noqa: E712
    it = df["type_name"] == "Interception"
    if not all_interceptions:
        it &= df["interception.outcome.name"].isin(INTERCEPTION_OK)
    return df[(br | it) & df["loc_x"].notna()].copy()


def recoveries_leading_to_shot(raw_events, rec):
    """Recoveries followed, in the same possession, by a shot of the same team.

    Why not simply "possession contains a shot": that gives 24 in the Clasico,
    but 4 of those sit AFTER the shot (scrambling after a save) and 5 belong to
    the opponent. Clean are only those with a higher event index AND the same
    team -> 15.
    """
    shots = collections.defaultdict(list)
    for e in raw_events:
        if e["type"]["name"] == "Shot":
            shots[e["possession"]].append(e)

    idx_to_poss = {e["id"]: (e["possession"], e["index"], e["team"]["name"])
                   for e in raw_events}

    rows = []
    for _, r in rec.iterrows():
        pid, idx, team = idx_to_poss[r["id"]]
        following = [s for s in shots.get(pid, [])
                     if s["index"] > idx and s["team"]["name"] == team]
        if following:
            s = following[0]
            d = dict(r)
            d["shooter"] = (s.get("player") or {}).get("name")
            d["shot_x"] = (s.get("location") or [None, None])[0]
            d["shot_y"] = (s.get("location") or [None, None])[1]
            d["xg"] = float((s.get("shot") or {}).get("statsbomb_xg") or 0.0)
            d["shot_outcome"] = (s.get("shot") or {}).get("outcome", {}).get("name")
            # Goal = shot outcome "Goal". Own goals are separate StatsBomb
            # events (Own Goal For/Against) and do not appear in this chain.
            d["goal"] = d["shot_outcome"] == "Goal"
            d["seconds_later"] = (s["minute"] * 60 + s["second"]) - (r["minute"] * 60 + r["second"])
            rows.append(d)
    return pd.DataFrame(rows)


def colour_map(names):
    return {n: PALETTE[i % len(PALETTE)] for i, n in enumerate(sorted(names))}


def _has_goal(sub):
    return "goal" in sub.columns and bool(sub["goal"].any())


def _label_minutes(ax, sub):
    for _, r in sub.iterrows():
        goal = bool(r.get("goal")) if "goal" in sub.columns else False
        if goal:
            ax.scatter(r["loc_x"], r["loc_y"], s=300, facecolors="none",
                       edgecolors="#f1c40f", linewidths=2.4, zorder=5)
        ax.annotate(f"{int(r['minute'])}'", xy=(r["loc_x"], r["loc_y"]),
                    xytext=(5, -9), textcoords="offset points",
                    fontsize=7.5, fontweight="bold" if goal else "normal",
                    color="#000000" if goal else "#333333", zorder=6)


def dot_map(sub, team, tag, out_path, with_minutes=False):
    names = sorted(sub["player_name"].unique())
    fmap = colour_map(names)
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    for n in names:
        s = sub[sub["player_name"] == n]
        ax.scatter(s["loc_x"], s["loc_y"], s=95, color=fmap[n],
                   edgecolors="black", linewidths=0.7, zorder=4,
                   label=f"{short_name(n)} ({len(s)})")
    if with_minutes:
        _label_minutes(ax, sub)
    draw_pitch(ax)
    direction_hint(ax)
    ax.set_title(f"Ball recoveries — {team} ({tag})   "
                 f"{len(sub)} recoveries, {len(names)} players"
                 + ("\n(gold ring = a goal came from this recovery)" if _has_goal(sub) else ""),
                 fontsize=11)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5),
              fontsize=8, frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_path


def both_map(sub, tag, out_path, with_minutes=False):
    teams = list(dict.fromkeys(sub["team_name"]))
    names = sorted(sub["player_name"].unique())
    fmap = colour_map(names)
    markers = ["o", "^"]
    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    for t, m in zip(teams, markers):
        s = sub[sub["team_name"] == t]
        for n in sorted(s["player_name"].unique()):
            p = s[s["player_name"] == n]
            ax.scatter(p["loc_x"], p["loc_y"], s=90, color=fmap[n], marker=m,
                       edgecolors="black", linewidths=0.7, zorder=4,
                       label=f"{short_name(n)} ({t.split()[0]}, {len(p)})")
    if with_minutes:
        _label_minutes(ax, sub)
    draw_pitch(ax)
    direction_hint(ax)
    ax.set_title(f"Ball recoveries, both teams — {tag}   "
                 f"(circle = {teams[0]}, triangle = {teams[1]}; colour = player)"
                 + ("\n(gold ring = a goal came from this recovery)" if _has_goal(sub) else ""),
                 fontsize=11)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5),
              fontsize=7.5, frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_path


def zone_map(df, rec, raw_events, tag, out_path):
    """Longitudinal distribution per team: did this team press high?

    A single mean hides a lot here, because goalkeeper recoveries deep in the
    own box pull the distribution left. So the figure shows the full
    distribution and marks the goalkeeper separately.
    """
    gk = {}
    for e in raw_events:
        if e["type"]["name"] == "Goal Keeper" and e.get("player"):
            gk.setdefault(e["team"]["name"], collections.Counter())[e["player"]["name"]] += 1
    keepers = {t: c.most_common(1)[0][0] for t, c in gk.items()}

    teams = list(dict.fromkeys(rec["team_name"]))
    colours = {"Barcelona": "#a50044", "Real Madrid": "#00529f"}
    fig, axes = plt.subplots(len(teams), 1, figsize=(11, 3.4 * len(teams)), sharex=True)
    if len(teams) == 1:
        axes = [axes]
    bins = np.arange(0, 121, 10)

    for ax, t in zip(axes, teams):
        s = rec[rec.team_name == t]
        xs = s["loc_x"].to_numpy()
        ax.hist(xs, bins=bins, color=colours.get(t, "#7f8c8d"), alpha=0.75,
                edgecolor="white")
        keeper = s[s.player_name == keepers.get(t)]
        if len(keeper):
            ax.hist(keeper["loc_x"].to_numpy(), bins=bins, color="#f1c40f",
                    alpha=0.95, edgecolor="white")
        ax.axvline(xs.mean(), color="black", lw=1.6, ls="--")
        ax.axvline(np.median(xs), color="black", lw=1.0, ls=":")
        ax.set_title(f"{t} — {len(s)} recoveries   "
                     f"mean {xs.mean():.0f} m, median {np.median(xs):.0f} m, "
                     f"sd {xs.std():.0f}"
                     + (f"   (yellow: goalkeeper {len(keeper)})" if len(keeper) else ""),
                     fontsize=10, loc="left")
        ax.set_ylabel("recoveries")
        ax.grid(axis="y", alpha=0.25)
        ax.axvspan(0, 40, color="#95a5a6", alpha=0.10)
        ax.axvspan(80, 120, color="#27ae60", alpha=0.10)

    axes[-1].set_xlabel("pitch length  —  0 = own goal  ·  120 = opponent goal")
    fig.suptitle("Where were balls won? Distribution along the pitch",
                 fontsize=12.5)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def write_csv(rows, path, with_shot):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        head = ["player", "team", "match_id", "minute", "x", "y", "type"]
        if with_shot:
            head += ["shooter", "shot_x", "shot_y", "xg", "shot_outcome",
                     "goal", "seconds_later"]
        fh.write(";".join(head) + "\n")

        def z(v):
            return "" if v is None else f"{v:.2f}".replace(".", ",")

        for r in sorted(rows, key=lambda x: (x["team"], x["minute"])):
            fields = [str(r["player"]), str(r["team"]), str(r["match_id"]),
                      str(r["minute"]), z(r["x"]), z(r["y"]), str(r["type"])]
            if with_shot:
                fields += [str(r["shooter"]), z(r["shot_x"]), z(r["shot_y"]),
                           "" if r["xg"] is None else f"{r['xg']:.3f}".replace(".", ","),
                           str(r["shot_outcome"]),
                           "yes" if r["goal"] else "no", str(r["seconds_later"])]
            fh.write(";".join(fields) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", help="single match id (e.g. 9924); default all")
    ap.add_argument("--with-failures", action="store_true")
    ap.add_argument("--all-interceptions", action="store_true")
    ap.add_argument("--only-shots", action="store_true",
                    help="only recoveries followed by a shot of the same team")
    ap.add_argument("--by-zone", action="store_true",
                    help="longitudinal distribution per team")
    args = ap.parse_args()

    files = event_files()
    if args.match:
        files = [f for f in files if match_id(f) == args.match]
        if not files:
            raise SystemExit(f"match {args.match} not found in {EVENTS}")
    if not files:
        raise SystemExit("No event files. Run: python3 data/get_data.py")

    tag = args.match or "all_matches"
    if args.only_shots:
        tag += "_shots"

    rows = []
    for f in files:
        df = load_match(f)
        rec = recoveries(df, args.with_failures, args.all_interceptions)
        if args.only_shots:
            with open(f, encoding="utf-8") as fh:
                raw = json.load(fh)
            rec = recoveries_leading_to_shot(raw, rec)
        for _, r in rec.iterrows():
            rows.append({
                "match_id": match_id(f), "player": r["player_name"],
                "team": r["team_name"], "minute": r["minute"],
                "x": r["loc_x"], "y": r["loc_y"], "type": r["type_name"],
                "shooter": r.get("shooter"), "xg": r.get("xg"),
                "shot_outcome": r.get("shot_outcome"),
                "goal": bool(r.get("goal", False)) if args.only_shots else None,
                "shot_x": r.get("shot_x"), "shot_y": r.get("shot_y"),
                "seconds_later": r.get("seconds_later"),
            })

    print(f"matches: {len(files)} | recoveries: {len(rows)}")
    agg = {}
    for r in rows:
        agg[(r["player"], r["team"])] = agg.get((r["player"], r["team"]), 0) + 1
    print("\n# recoveries per player")
    for (p, t), n in sorted(agg.items(), key=lambda kv: -kv[1])[:20]:
        print(f"  {short_name(p):26} {t[:16]:16} {n:4d}")

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    if args.match and not args.by_zone:
        df = load_match(files[0])
        rec = recoveries(df, args.with_failures, args.all_interceptions)
        if args.only_shots:
            with open(files[0], encoding="utf-8") as fh:
                raw = json.load(fh)
            rec = recoveries_leading_to_shot(raw, rec)
        for t in list(dict.fromkeys(rec["team_name"])):
            sub = rec[rec["team_name"] == t]
            out = os.path.join(OUT_DIR, f"recoveries_{tag}_{t.split()[0]}.png")
            dot_map(sub, t, tag, out, with_minutes=args.only_shots)
            print(f"map: {out}")
        out = os.path.join(OUT_DIR, f"recoveries_{tag}_both.png")
        both_map(rec, tag, out, with_minutes=args.only_shots)
        print(f"map: {out}")

    if args.by_zone:
        df = load_match(files[0])
        rec = recoveries(df, args.with_failures, args.all_interceptions)
        with open(files[0], encoding="utf-8") as fh:
            raw = json.load(fh)
        out = os.path.join(OUT_DIR, f"recovery_zones_{tag}.png")
        zone_map(df, rec, raw, tag, out)
        print(f"map: {out}")

    csv = os.path.join(DATA, f"recoveries_{tag}.csv")
    write_csv(rows, csv, args.only_shots)
    print(f"\nCSV: {csv}")


if __name__ == "__main__":
    main()
