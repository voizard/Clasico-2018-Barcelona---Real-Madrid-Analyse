#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Draw a football pitch in StatsBomb coordinates (120 x 80, origin bottom-left).

Shared by all map scripts so every figure looks the same. Extracted from the
original heatmap module, because the heatmap analyses are not part of this
repository.
"""
from __future__ import annotations

from matplotlib.patches import Arc, Circle, Rectangle

PITCH_X, PITCH_Y = 120.0, 80.0


def draw_pitch(ax, lw=1.0, color="#3a3a3a"):
    ax.add_patch(Rectangle((0, 0), PITCH_X, PITCH_Y, fill=False, ec=color, lw=lw))
    ax.plot([PITCH_X / 2, PITCH_X / 2], [0, PITCH_Y], color=color, lw=lw)
    ax.add_patch(Circle((PITCH_X / 2, PITCH_Y / 2), 9.15, fill=False, ec=color, lw=lw))
    ax.add_patch(Circle((PITCH_X / 2, PITCH_Y / 2), 0.4, color=color))

    # Penalty area, six-yard box and spot, both sides
    for side in (0, 1):
        x0 = 0 if side == 0 else PITCH_X - 18
        ax.add_patch(Rectangle((x0, PITCH_Y / 2 - 20.16), 18, 40.32,
                               fill=False, ec=color, lw=lw))
        x6 = 0 if side == 0 else PITCH_X - 6
        ax.add_patch(Rectangle((x6, PITCH_Y / 2 - 9.16), 6, 18.32,
                               fill=False, ec=color, lw=lw))
        spot = 11 if side == 0 else PITCH_X - 11
        ax.add_patch(Circle((spot, PITCH_Y / 2), 0.4, color=color))
        if side == 0:
            ax.add_patch(Arc((spot, PITCH_Y / 2), 18.3, 18.3, angle=0,
                             theta1=-53, theta2=53, ec=color, lw=lw))
        else:
            ax.add_patch(Arc((spot, PITCH_Y / 2), 18.3, 18.3, angle=0,
                             theta1=127, theta2=233, ec=color, lw=lw))
    ax.set_xlim(-2, PITCH_X + 2)
    ax.set_ylim(-2, PITCH_Y + 2)
    ax.set_aspect("equal")
    ax.axis("off")


def direction_hint(ax):
    """Make the reading direction explicit: own goal left, attack to the right.

    StatsBomb already normalises coordinates so that every team attacks to the
    right (verified across all matches: each goalkeeper sits at x ~ 2-6 in both
    halves). The hint makes that visible so it cannot be confused with the real
    side switch at half time.
    """
    ax.set_ylim(-2, PITCH_Y + 9)
    ax.annotate("", xy=(PITCH_X - 6, PITCH_Y + 5),
                xytext=(PITCH_X - 40, PITCH_Y + 5),
                arrowprops=dict(arrowstyle="-|>", color="#1f4e79", lw=2.4))
    ax.text(PITCH_X - 42, PITCH_Y + 5, "attack direction", ha="right",
            va="center", fontsize=9.5, color="#1f4e79", fontweight="bold")
    ax.text(2, PITCH_Y + 5, "\u25c0 own goal", ha="left", va="center",
            fontsize=9, color="#7f8c8d")
