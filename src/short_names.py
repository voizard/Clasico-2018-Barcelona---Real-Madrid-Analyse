#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recognisable short name from a full StatsBomb name.

StatsBomb delivers full names ("Lionel Andres Messi Cuccittini"). Taking the
last word yields nonsense ("Cuccittini"), and a heuristic fails on Iberian
double names ("Jordi Alba Ramos" -> "Ramos"). So a curated dictionary
(short_names.json) covers the names present in the data; unknown names fall
back to a simple rule.
"""
from __future__ import annotations

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "short_names.json"), encoding="utf-8") as _fh:
    SHORT_NAMES = json.load(_fh)


def short_name(full):
    if not isinstance(full, str):
        return full
    if full in SHORT_NAMES:
        return SHORT_NAMES[full]
    parts = full.split()
    return parts[-1] if parts else full
