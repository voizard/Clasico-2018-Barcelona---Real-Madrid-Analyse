#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repo-relative paths, so every script works from any working directory."""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS = os.path.join(ROOT, "data", "events")
FIGURES = os.path.join(ROOT, "figures")
DATA = os.path.join(ROOT, "data")


def event_files():
    """All downloaded event files, sorted by match id."""
    if not os.path.isdir(EVENTS):
        return []
    return sorted(os.path.join(EVENTS, f) for f in os.listdir(EVENTS)
                  if f.endswith(".json"))


def match_id(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]
