# Data

The raw match data used by this project is **StatsBomb Open Data** and is *not*
stored in this repository.

## Source

- Project: <https://github.com/statsbomb/open-data>
- Events path: `data/events/<match_id>.json`
- Raw URL pattern: `https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/<match_id>.json`

## Licence

StatsBomb Open Data is free to use for **non-commercial** purposes **with
attribution to StatsBomb**. See the `LICENSE` file in the open-data repository
before reusing the data. This repository only ships the analysis code; the data
stays with StatsBomb.

## Fetching it

```bash
python3 data/get_data.py            # downloads all 22 files into data/events/
python3 data/get_data.py --force    # re-downloads
```

Each file is a JSON array of events for one match (roughly 3,000–4,000 events,
about 3 MB). `data/events/` is listed in `.gitignore`, so `git status` stays
clean after a download.

## Matches used

| Match id | Competition | Fixture |
|---|---|---|
| 9754 | La Liga 2017/18 | Real Sociedad 2–4 Barcelona |
| 9765 | La Liga 2017/18 | Real Betis 0–5 Barcelona |
| 9774 | La Liga 2017/18 | Barcelona 2–1 Deportivo Alavés |
| 9783 | La Liga 2017/18 | Espanyol 1–1 Barcelona |
| 9794 | La Liga 2017/18 | Barcelona 0–0 Getafe |
| 9799 | La Liga 2017/18 | Eibar 0–2 Barcelona |
| 9880 | La Liga 2017/18 | Barcelona 2–1 Valencia |
| 9889 | La Liga 2017/18 | Celta Vigo 2–2 Barcelona |
| 9912 | La Liga 2017/18 | Deportivo La Coruña 2–4 Barcelona |
| 9924 | La Liga 2017/18 | Barcelona 2–2 Real Madrid |
| 9928 | La Liga 2017/18 | Barcelona 5–1 Villarreal |
| 9948 | La Liga 2017/18 | Barcelona 1–0 Real Sociedad |
| 7567 | World Cup 2018 | South Korea 2–0 Germany |
| 7568 | World Cup 2018 | Switzerland 2–2 Costa Rica |
| 7569 | World Cup 2018 | Panama 1–2 Tunisia |
| 7570 | World Cup 2018 | England 0–1 Belgium |
| 9811 | La Liga 2017/18 | Barcelona 6–1 Girona |
| 9827 | La Liga 2017/18 | Las Palmas 1–1 Barcelona |
| 9837 | La Liga 2017/18 | Barcelona 1–0 Atlético Madrid |
| 9855 | La Liga 2017/18 | Barcelona 2–0 Athletic Club |
| 9860 | La Liga 2017/18 | Sevilla 2–2 Barcelona |
| 9870 | La Liga 2017/18 | Barcelona 3–1 Leganés |

`src/identify_matches.py` re-derives this list (teams, score, shots, xG) directly
from the downloaded files — run it to confirm the data matches the table above.
