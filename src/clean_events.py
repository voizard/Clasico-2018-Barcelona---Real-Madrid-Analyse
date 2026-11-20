#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load StatsBomb event JSON into a tidy pandas DataFrame.

Why a helper at all: fields like location / pass.end_location / ... are JSON
lists. pandas stores them as object columns holding Python lists — so columns
such as 'pass.end_location.1' are not addressable and comparisons/plots fail.
This module unpacks them once into numeric columns.

Rules:
  * list -> x/y (or end_x/end_y), missing values -> NaN
  * 3D end points (Shot/Carry: StatsBomb delivers [x, y, z]) -> x/y only
  * rows without a location are kept (Starting XI, Half Start, ...): these are
    valid events that simply carry no coordinate
  * direction is normalised to "team attacks to the right" (mirror x -> 120-x,
    y -> 80-y) so maps are consistent across halves and teams. Verified: the
    open-data files are already oriented this way, so nothing is mirrored.
"""
from __future__ import annotations

import json

import pandas as pd

PITCH_X, PITCH_Y = 120.0, 80.0

# Events without a coordinate are normal, not broken.
NO_LOCATION_TYPES = {
    "Starting XI", "Half Start", "Half End", "Substitution",
    "Tactical Shift", "Player On", "Player Off", "Injury Stoppage",
    "Bad Behaviour", "Camera On", "Camera off",
}


def _xy(value):
    """List -> (x, y); anything else -> (NaN, NaN)."""
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        x, y = value[0], value[1]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return float(x), float(y)
    return (float("nan"), float("nan"))


def load_match(path: str) -> pd.DataFrame:
    with open(path, encoding="utf-8") as fh:
        events = json.load(fh)

    df = pd.json_normalize(events)

    # --- unpack coordinates ----------------------------------------------
    for col, out in (("location", "loc"), ("pass.end_location", "pass_end"),
                     ("carry.end_location", "carry_end"),
                     ("shot.end_location", "shot_end"),
                     ("goalkeeper.end_location", "gk_end")):
        if col in df.columns:
            xy = df[col].map(_xy)
            df[f"{out}_x"] = [p[0] for p in xy]
            df[f"{out}_y"] = [p[1] for p in xy]
        else:
            df[f"{out}_x"] = df[f"{out}_y"] = float("nan")

    df["type_name"] = df.get("type.name", pd.Series(index=df.index, dtype=object))
    df["player_name"] = df.get("player.name", pd.Series(index=df.index, dtype=object))
    df["team_name"] = df.get("team.name", pd.Series(index=df.index, dtype=object))

    df["has_location"] = df["loc_x"].notna()
    df["no_location_ok"] = df["type_name"].isin(NO_LOCATION_TYPES)

    df = normalise_direction(df)
    return df


def _attacking_right(df: pd.DataFrame, team_id) -> bool:
    """A team shoots at the right goal if its shots sit on average right of centre."""
    shots = df[(df["team.id"] == team_id) & (df["type_name"] == "Shot")]
    if shots.empty or shots["loc_x"].isna().all():
        return True
    return shots["loc_x"].mean() > PITCH_X / 2


def normalise_direction(df: pd.DataFrame) -> pd.DataFrame:
    """Mirror events so that every team attacks to the right."""
    flip = {}
    for tid in df["team.id"].dropna().unique():
        flip[tid] = not _attacking_right(df, tid)
    df = df.copy()
    df["flipped"] = df["team.id"].map(flip).fillna(False)
    m = df["flipped"]
    for c in ("loc_x", "pass_end_x", "carry_end_x", "shot_end_x", "gk_end_x"):
        df[c] = df[c].where(~m, PITCH_X - df[c])
    for c in ("loc_y", "pass_end_y", "carry_end_y", "shot_end_y", "gk_end_y"):
        df[c] = df[c].where(~m, PITCH_Y - df[c])
    return df


def check(df: pd.DataFrame) -> dict:
    """Short data-quality report."""
    return {
        "events": len(df),
        "with_coordinate": int(df["has_location"].sum()),
        "without_coordinate": int((~df["has_location"]).sum()),
        "without_coordinate_expected": int((~df["has_location"] & df["no_location_ok"]).sum()),
        "without_coordinate_unexpected": int((~df["has_location"] & ~df["no_location_ok"]).sum()),
        "x_out_of_range": int(((df["loc_x"] < 0) | (df["loc_x"] > PITCH_X)).sum()),
        "y_out_of_range": int(((df["loc_y"] < 0) | (df["loc_y"] > PITCH_Y)).sum()),
    }


if __name__ == "__main__":
    import sys
    p = sys.argv[1]
    d = load_match(p)
    for k, v in check(d).items():
        print(f"{k:32} {v}")
