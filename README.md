# Clásico & La Liga 2017/18 — StatsBomb Event Analysis

Event-level analysis of **FC Barcelona's 2017/18 La Liga season** (plus the 2018
World Cup group stage), built on [StatsBomb Open Data](https://github.com/statsbomb/open-data).
Four focused views: **crosses**, **key passes**, **pass networks** and **ball
recoveries**.

The headline question was simple: *the Clásico ended 2–2 — but who actually
played better, and in what way?*

---

## Key findings (Clásico 9924: Barcelona 2–2 Real Madrid)

| | Barcelona | Real Madrid |
|---|---|---|
| **Crosses** | 5 (2 completed) | **20** (6 completed) |
| Goals from crosses | **1** | 0 |
| **Key passes** | 8 | **15** |
| Goals from key passes | 2 | 2 |
| xG from key passes | 0.89 | **1.64** |
| Recoveries in the opponent's half, 1st half (11 v 11) | 43 % | 43 % |
| Mean `Pressure` position, 1st half (11 v 11) | **57 m** | 53 m |
| Busiest passer (named connections) | **Rakitić (159)** | Modrić (148) |

**1. Real Madrid crossed four times as often and got nothing from it.**
20 crosses to Barcelona's 5 — but Real's crosses produced only two shots
(xG 0.10 and 0.03) and no goal. Barcelona's single meaningful cross (Sergi
Roberto, 9') was finished by Suárez. *Volume without threat.*

**2. The pressing story is a sending-off story — Barcelona pressed higher until
they went a man down.**
Taken over the whole match, Real Madrid looks like the higher-pressing side:
it recovered 46 % of its balls in Barcelona's half (Barça 36 %) and its
`Pressure` events averaged 58 m vs 52 m. But that whole-match view is an
artefact of the second half. **Sergi Roberto was sent off in the 46th minute**
(`match_context.py`), so Barcelona played the entire second half with ten men —
and the split by half shows exactly what that did:

| | 1st half (11 v 11) | 2nd half (Barça a man down) |
|---|---|---|
| Barça recoveries — mean position | **55.2 m** | 41.6 m |
| Real recoveries — mean position | 50.5 m | 52.0 m |
| Barça `Pressure` events (mean x) | 44 (57.3 m) | 46 (46.4 m) |
| Real `Pressure` events (mean x) | 53 (52.5 m) | **89 (61.4 m)** |

At **11 v 11 Barcelona actually pressed slightly higher** (Pressure mean 57.3 m
vs 52.5 m; recoveries 55.2 m vs 50.5 m). Real's dominance of territory appears
only after the red card — 89 pressure events to Barça's 46 in the second half.
So the honest reading is not "Real pressed higher" but "the sending-off handed
Real the pitch".

Two further artefacts worth knowing before reading the whole-match averages:
Barcelona's recovery distribution is **bimodal** — a cluster deep in its own box
*and* one in the attacking third — and the deep cluster is mostly the goalkeeper:
5 of its 8 recoveries in its own box are ter Stegen distributions, not pressing.
Excluding keepers, the two teams' mean recovery positions over the whole match
are almost identical (Barça 54.4 m, Real 52.3 m).

**3. The goals were made, not crossed.**
All four goals came from open-play passes, and the key-pass map shows exactly
who fed whom: Suárez ← Sergi Roberto (9'), Ronaldo ← Benzema (14'),
Messi ← Suárez (51'), Bale ← Asensio (71'). Asensio delivered five crosses and
assisted a goal with a pass that StatsBomb does *not* classify as a cross — the
crossing volume was never the route to goal.

Across **all 22 matches**, Barcelona attempted 467 crosses (158 completed, 100
leading to a shot, 14 goals). The most productive crossers were Alba
(30 crosses, 12 completed, 8 shots, 1 goal), Suárez (18/10/7) and Dembélé
(17/9/6, 2 goals).

**4. The pass networks show the shape behind the numbers.**
The mean position of each player's ball actions *is* the structural finding:

- **Casemiro played as a third centre-back.** His mean position sits at x = 45.9 m,
  right on the centre-back line (Ramos 42.5, Varane 41.2), while Kroos (63.0) and
  Modrić (65.9) are 17–20 m further forward. His most frequent passes go sideways
  and back — Ramos 9×, Modrić 9× — not forward.
- **Marcelo held the ball high and wide.** Mean position x = 70.2 m, y = 12.6
  (far left touchline), with 242 ball actions (second only to Modrić's 243) and
  72 passes. The right-side triangle Ramos → Marcelo (14×), Marcelo → Kroos
  (13×), Modrić → Marcelo (10×), Kroos → Marcelo (9×) is the visible passing row.
- **Rakitić was Barcelona's central link — and the busiest player on the pitch.**
  He is involved in 159 named pass connections (80 out, 79 in), more than anyone
  on either team (Modrić 148, Busquets 147, Kroos 139), and appears in six of
  Barcelona's fifteen most frequent connections (Rakitić → Messi 20×, Rakitić →
  Busquets 16×, Busquets → Rakitić 14×, Messi → Rakitić 14×, Iniesta → Rakitić
  13×, Rakitić → Iniesta 10×).
- **Barcelona's engine was a triangle.** Busquets, Rakitić and Messi form the
  strongest three-man triangle in the entire match: 90 passes among the three
  (Rakitić ↔ Messi 34, Busquets ↔ Rakitić 30, Busquets ↔ Messi 26). The best
  triangle Real Madrid can field — Benzema / Kroos / Marcelo — reaches only 64.
  The triangle is a spine, not a closed unit: 251 of the trio's 431 connections
  still go to the rest of the team (Iniesta 56, Sergi Roberto 36, Umtiti and
  Piqué 29 each).

---

## What happened in the match (Clásico 9924)

The structural findings above only make sense against the match narrative, so
`src/match_context.py` extracts it from the events:

**Goals.** 9' Suárez (assist Sergi Roberto) 1–0 · 14' Ronaldo (assist Benzema)
1–1 · 51' Messi (assist Suárez) 2–1 · 71' Bale (assist Asensio) 2–2.

**Cards** (9 yellow, 1 red). 11' Isco · 30' Varane · 43' Suárez and 43' Ramos
(both for dissent) · 44' Messi · **46' Sergi Roberto (red)** · 75' Bale ·
76' Marcelo · 84' Rakitić. The red card is the pivotal event of the match: it
turned the second half into eleven against ten.

**Substitutions.** 45' Real: Ronaldo → Asensio (Real had an injury stoppage in
the 14th minute; Ronaldo did not return after the break) · 45' Barça: Coutinho →
Semedo · 56' Barça: Iniesta → Paulinho · 67' Real: Isco → Vázquez · 83' Real:
Kroos → Kovačić · 91' Barça: Suárez → Alcácer.

**Injury stoppages.** 14' and 15' (Ronaldo and Barça), 58', and two in the 86th
minute.

**Fouls.** Barcelona 9, Real Madrid 22 — consistent with a team chasing the game
with ten men.

**Half-by-half split.** Possession: Barça 56 % / 44 % in the first half, then
41 % / 59 % after the break. Crosses: Barça 4, Real 10 (first half) then Barça 1,
Real 10. Shots: 4 v 9 then 7 v 8. xG: 0.27 v 1.31 then 0.74 v 0.46.

The early substitutions also matter for the pass networks: Coutinho (44 min) and
Iniesta (55 min) left the pitch early, and Ronaldo (47 min) did not return — so
their connection totals are low by minutes played, not by involvement.

---

## Figures

| File | What it shows |
|---|---|
| `figures/crosses_9924_Barcelona.png` | Barcelona's 5 crosses; green = completed, dot = origin, arrow head = target |
| `figures/crosses_9924_Real.png` | Real Madrid's 20 crosses |
| `figures/key_passes_9924_Barcelona.png` | Key passes; **gold + labelled = goal from this pass**, red = dangerous (xG ≥ 0.10), grey = other |
| `figures/key_passes_9924_Real.png` | same for Real Madrid |
| `figures/pass_network_9924_Barcelona.png` | pass network; dot = mean position, line thickness = pass count |
| `figures/pass_network_9924_Real.png` | same for Real Madrid — the Casemiro / Marcelo shape |
| `figures/recoveries_9924_shots_*.png` | recoveries followed, in the same possession, by a shot of the same team |
| `figures/recovery_zones_9924.png` | longitudinal distribution per team — the pressing-height question |
| `figures/recovery_zones_9924_by_half.png` | the same, split by half: Barcelona is the higher line at 11 v 11, and only drops after the red card |

All maps share one reading direction: **own goal on the left, attack to the
right**. StatsBomb already normalises coordinates this way (verified: every
goalkeeper sits at x ≈ 2–6 in *both* halves, in all 22 matches), so nothing is
mirrored — the arrow at the top just makes it visible.

---

## Data source

The raw data is **StatsBomb Open Data**, not redistributed here. It is published
at <https://github.com/statsbomb/open-data> and is free to use for
**non-commercial** purposes **with attribution to StatsBomb**. Read that
repository's `LICENSE` before reusing it.

`data/get_data.py` fetches the 22 event files used here into `data/events/`
(which is git-ignored). Each file is one match as JSON:

```bash
python3 data/get_data.py            # fetch everything, skips files already present
```

The 22 matches: 18 FC Barcelona La Liga 2017/18 fixtures, plus the four 2018
World Cup group-stage games (7567–7570) as a comparison set.

---

## Methods

Everything is computed from the raw events; nothing is hard-coded.

**Crosses.** StatsBomb marks a pass with `pass.cross == true` (25 of 1161 passes
in the Clásico). *Completed* means the pass found a target (no `pass.outcome`).
A cross is counted as leading to a shot via `pass.assisted_shot_id`, and to a
goal if that shot's outcome is `Goal`.

**Key passes.** A pass immediately followed by a shot. StatsBomb links this both
ways — `shot.key_pass_id` ↔ `pass.assisted_shot_id` — and both directions agree
exactly in the Clásico, so we read `shot.key_pass_id`. *Dangerous* = the
resulting shot had xG ≥ 0.10 (threshold configurable with `--xg`).

**Ball recoveries.** "Ball loss"/"recovery" is not a single field. A recovery is
either a `Ball Recovery` event (excluding those flagged `recovery_failure`) or an
`Interception` won (`Won` / `Success In Play`). In the Clásico that is 69 + 14 =
83. For the pressing question we also count raw `Pressure` events, which are a
cleaner signal than recoveries because they are not biased by the goalkeeper.

**Pass network.** Each player sits at the mean position of his ball actions
(`loc_x`, `loc_y` over every event with a coordinate); lines connect the pairs
that passed to each other most often, using StatsBomb's `pass.recipient` field
(filled for 1081 of 1161 passes in the Clásico; passes without a recipient are
skipped, not guessed).

**Match context.** `match_context.py` reads goals (`Shot` with outcome `Goal`,
plus `Own Goal For`), cards (`foul_committed.card`, `bad_behaviour.card`),
substitutions, injury stoppages and fouls straight from the events, and splits
possession, shots, xG and crosses by half (StatsBomb `period`).

**Direction.** `src/clean_events.py` unpacks StatsBomb's list-valued coordinate
fields into numeric columns and normalises direction, but verified that the
open-data files are already oriented correctly.

---

## Limitations

- **One Real Madrid match.** Real Madrid appears in exactly **one** of the 22
  files — the Clásico. Everything said about Real Madrid rests on that single
  game and is a description of *that match*, not of a season-long pattern.
  Barcelona appears in 18 matches; the cross totals across all matches are
  therefore Barcelona-heavy by construction.
- **Own goals are not in the pass chain.** StatsBomb records own goals as their
  own events (`Own Goal For` / `Own Goal Against`). A goal that followed an
  own-goal deflection would therefore *not* be counted as "goal from a key
  pass". No such case occurs in the Clásico.
- **Recovery ≠ pressing, strictly.** A recovery deep in your own half can simply
  be the goalkeeper collecting the ball. The `--by-zone` figure isolates the
  keeper for this reason; treat the raw mean with care.
- **"Dangerous" is a chosen threshold.** xG ≥ 0.10 is a convention, not a fact.
  Re-run with `--xg 0.05` or `--xg 0.15` to see how sensitive the count is.

---

## Structure

```
.
├── README.md
├── LICENSE
├── requirements.txt
├── data/
│   ├── get_data.py          # fetches the raw StatsBomb files
│   └── README.md            # data source and licence note
├── src/
│   ├── clean_events.py      # JSON -> tidy DataFrame, direction normalisation
│   ├── pitch.py             # pitch drawing + direction hint
│   ├── short_names.py       # full StatsBomb name -> short name
│   ├── paths.py             # repo-relative paths
│   ├── identify_matches.py  # teams, score, shots, xG per file
│   ├── match_context.py     # goals, cards, subs, injuries, half split
│   ├── crosses.py           # the analyses
│   ├── key_passes.py
│   ├── pass_network.py
│   └── recoveries.py
└── figures/                 # generated PNGs
```

## Reproduction

```bash
pip install -r requirements.txt
python3 data/get_data.py                 # 22 event files -> data/events/
cd src
python3 identify_matches.py              # sanity check: who played whom
python3 match_context.py --match 9924    # goals, cards, subs, half split
python3 crosses.py --match 9924          # the Clásico, with per-team maps
python3 key_passes.py --match 9924
python3 pass_network.py --match 9924
python3 recoveries.py --match 9924 --only-shots
python3 recoveries.py --match 9924 --by-zone
python3 recoveries.py --match 9924 --by-half   # the sending-off story
python3 crosses.py                       # season summary across all 22 matches
```

CSVs land in `data/`, figures in `figures/`. The CSVs use semicolon separators
and a decimal comma (Power BI / German locale); if you parse them yourself,
strip the BOM.

---

## Licence

Code: MIT (see `LICENSE`). Data: StatsBomb Open Data, under StatsBomb's own
terms — non-commercial use, attribution required.
