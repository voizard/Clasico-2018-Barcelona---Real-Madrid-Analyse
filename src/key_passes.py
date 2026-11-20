#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Key passes (StatsBomb).

Definition (verified against the raw data, not guessed):
  * Key pass = a pass immediately followed by a shot. StatsBomb links this both
    ways: shot.key_pass_id <-> pass.assisted_shot_id. In the Clasico 9924 both
    directions agree exactly, so we read shot.key_pass_id.
  * "Dangerous" is NOT the same as "shot": the Clasico had 28 shots but only 23
    with a preceding pass. We therefore report two numbers:
        passes        = all key passes
        dangerous     = key passes leading to a shot with xG >= threshold (0.10)
        xg_total      = sum of xG of those shots

Map (one per team):
  * dot = pass origin, arrow head = pass target, star = shot location
  * gold + thick = a goal was scored from this pass, labelled with scorer and
    provider; red = dangerous (xG >= threshold); grey/thin = other key pass
  * only goals are labelled — labelling every shot made the first version
    unreadable at 23 passes
  * gold label boxes are nudged automatically so two of them cannot overlap

Usage:
    python3 src/key_passes.py                 # all matches, summary
    python3 src/key_passes.py --match 9924    # one match, with per-team maps
    python3 src/key_passes.py --xg 0.15       # different "dangerous" threshold
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp

from clean_events import load_match
from paths import DATA, FIGURES, EVENTS, event_files, match_id
from pitch import draw_pitch, direction_hint
from short_names import short_name

OUT_DIR = FIGURES


def key_passes(path, xg_threshold=0.10):
    with open(path, encoding="utf-8") as fh:
        ev = json.load(fh)
    byid = {e["id"]: e for e in ev}

    rows = []
    for e in ev:
        if e["type"]["name"] != "Shot":
            continue
        kp_id = (e.get("shot") or {}).get("key_pass_id")
        if not kp_id:
            continue
        kp = byid.get(kp_id)
        if kp is None or kp["type"]["name"] != "Pass":
            continue
        xg = (e.get("shot") or {}).get("statsbomb_xg") or 0.0
        rows.append({
            "player": (kp.get("player") or {}).get("name"),
            "team": kp["team"]["name"],
            "team_shooter": e["team"]["name"],
            "minute": kp["minute"],
            "pass_x": (kp.get("location") or [None, None])[0],
            "pass_y": (kp.get("location") or [None, None])[1],
            "target_x": (kp["pass"].get("end_location") or [None, None])[0],
            "target_y": (kp["pass"].get("end_location") or [None, None])[1],
            "shooter": (e.get("player") or {}).get("name"),
            "shot_x": (e.get("location") or [None, None])[0],
            "shot_y": (e.get("location") or [None, None])[1],
            "xg": float(xg),
            "dangerous": bool(float(xg) >= xg_threshold),
            "outcome": (e.get("shot") or {}).get("outcome", {}).get("name"),
        })
    return rows


def map_for_team(rows, team, tag, out_path, xg_threshold):
    sub = [r for r in rows if r["team"] == team]
    if not sub:
        return None
    # Draw goals last so they sit on top.
    sub = sorted(sub, key=lambda r: (r["outcome"] == "Goal"))

    fig, ax = plt.subplots(figsize=(10.4, 7.4))
    n_goal = n_danger = 0
    xg_total = 0.0
    goal_notes = []
    goal_anns = []

    for r in sub:
        if None in (r["pass_x"], r["pass_y"], r["target_x"], r["target_y"]):
            continue
        xg_total += r["xg"]
        goal = r["outcome"] == "Goal"
        danger = r["dangerous"]
        if goal:
            colour, lw, alpha, z = "#f1c40f", 3.4, 1.0, 8
            n_goal += 1
        elif danger:
            colour, lw, alpha, z = "#c0392b", 2.0, 0.85, 4
            n_danger += 1
        else:
            colour, lw, alpha, z = "#95a5a6", 1.1, 0.45, 2

        ax.annotate("", xy=(r["target_x"], r["target_y"]),
                    xytext=(r["pass_x"], r["pass_y"]),
                    arrowprops=dict(arrowstyle="-|>", color=colour, lw=lw,
                                    alpha=alpha, shrinkA=0, shrinkB=0), zorder=z)
        ax.scatter(r["pass_x"], r["pass_y"], s=70 if goal else 22,
                   color="#1f4e79" if not goal else "#b7950b",
                   zorder=z + 1, edgecolors="white", linewidths=0.6)
        if r["shot_x"] is not None:
            ax.scatter(r["shot_x"], r["shot_y"], s=330 if goal else 120,
                       marker="*", color=colour, zorder=z + 1,
                       edgecolors="black" if goal else "#666666",
                       linewidths=1.1 if goal else 0.5)
        if goal:
            ann = ax.annotate(f"GOAL {short_name(r['shooter'])} {r['minute']}'\n"
                              f"assist: {short_name(r['player'])}",
                              xy=(r["shot_x"], r["shot_y"]),
                              xytext=(11, 11), textcoords="offset points",
                              fontsize=8.5, fontweight="bold", color="#7d6608",
                              zorder=9,
                              bbox=dict(boxstyle="round,pad=0.28", fc="#fffbe6",
                                        ec="#f1c40f", lw=1.0))
            goal_anns.append(ann)
            goal_notes.append(f"{r['minute']}' {short_name(r['shooter'])} "
                              f"\u2190 {short_name(r['player'])} (xG {r['xg']:.2f})")
        elif danger:
            ax.annotate(f"{short_name(r['player'])} {r['minute']}'",
                        xy=(r["pass_x"], r["pass_y"]),
                        xytext=(-6, 8), textcoords="offset points",
                        fontsize=7.6, color="#922b21", ha="right", zorder=9,
                        bbox=dict(boxstyle="round,pad=0.18", fc="white",
                                  ec="#c0392b", lw=0.6, alpha=0.88))

    draw_pitch(ax)
    direction_hint(ax)

    # Goal boxes must not overlap: try candidate positions, keep the first free.
    if goal_anns:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        candidates = [(11, 11), (11, -46), (-172, 11), (-172, -46),
                      (11, 46), (-172, 46)]
        taken = []
        for ann in goal_anns:
            for cand in candidates:
                ann.xyann = cand
                bb = ann.get_window_extent(renderer)
                if not any(bb.overlaps(b) for b in taken):
                    break
            taken.append(ann.get_window_extent(renderer))

    ax.set_title(f"Key passes — {team} ({tag})   {len(sub)} key passes, "
                 f"{n_danger} dangerous (xG \u2265 {xg_threshold:.2f}), "
                 f"{n_goal} goals   |   xG total {xg_total:.2f}", fontsize=11)

    handles = [
        mp.Patch(fc="#f1c40f", ec="black", lw=0.6,
                 label="goal from this pass (scorer + assist)"),
        mp.Patch(fc="#c0392b", ec="black", lw=0.6,
                 label=f"dangerous (xG \u2265 {xg_threshold:.2f}) — name at pass origin"),
        mp.Patch(fc="#95a5a6", ec="black", lw=0.6, label="other key pass"),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, frameon=True,
              bbox_to_anchor=(0.0, 0.0), borderaxespad=0.2)
    if goal_notes:
        ax.text(1.0, -0.055, "goals: " + "  ·  ".join(goal_notes),
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                color="#7d6608")

    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_path


def write_csv(rows, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        fh.write("player;team;match_id;minute;pass_x;pass_y;target_x;target_y;"
                 "shooter;shot_x;shot_y;xg;dangerous;goal;outcome\n")

        def z(v, n=2):
            return "" if v is None else f"{v:.{n}f}".replace(".", ",")

        for r in sorted(rows, key=lambda x: (x["team"], -x["xg"])):
            fh.write(";".join([
                str(r["player"]), str(r["team"]), str(r["match_id"]),
                str(r["minute"]), z(r["pass_x"]), z(r["pass_y"]),
                z(r["target_x"]), z(r["target_y"]), str(r["shooter"]),
                z(r["shot_x"]), z(r["shot_y"]), z(r["xg"], 3),
                "yes" if r["dangerous"] else "no",
                "yes" if r["outcome"] == "Goal" else "no",
                str(r["outcome"] or ""),
            ]) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", help="single match id (e.g. 9924); default all")
    ap.add_argument("--xg", type=float, default=0.10,
                    help="threshold for 'dangerous' (default 0.10)")
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
        for r in key_passes(f, args.xg):
            r["match_id"] = match_id(f)
            all_rows.append(r)

    # Sanity check: provider and shooter must be on the same team.
    mismatched = [r for r in all_rows if r["team"] != r["team_shooter"]]
    print(f"provider/shooter same team in all cases: {not mismatched}")
    print(f"matches: {len(files)} | key passes: {len(all_rows)}")

    agg = {}
    for r in all_rows:
        a = agg.setdefault((r["player"], r["team"]),
                           {"passes": 0, "dangerous": 0, "xg": 0.0})
        a["passes"] += 1
        a["dangerous"] += int(r["dangerous"])
        a["xg"] += r["xg"]
    print("\n# key passes per player")
    for (p, t), a in sorted(agg.items(),
                            key=lambda kv: (-kv[1]["dangerous"], -kv[1]["xg"]))[:20]:
        print(f"  {short_name(p):24} {t[:16]:16} passes {a['passes']:3d} | "
              f"dangerous {a['dangerous']:3d} | xG {a['xg']:.2f}")

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    tag = args.match or "all_matches"
    if args.match:
        for t in sorted({r["team"] for r in all_rows}):
            out = os.path.join(OUT_DIR, f"key_passes_{tag}_{t.split()[0]}.png")
            if map_for_team(all_rows, t, tag, out, args.xg):
                print(f"map: {out}")
    csv = os.path.join(DATA, f"key_passes_{tag}.csv")
    write_csv(all_rows, csv)
    print(f"\nCSV: {csv}")


if __name__ == "__main__":
    main()
