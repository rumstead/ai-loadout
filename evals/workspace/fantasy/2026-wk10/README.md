# Fantasy snapshot: 2026 week 10

Everything the waiver sweep and start/sit need for week 10 of the 2026 season,
saved on Tuesday, November 10, 2026, after week 9 and before waivers ran.
League names, league IDs and every owner but the user's are anonymized. Use
these files in place of the live sources, and treat `news.md` as the only news.
Write any scratch files outside this folder.

## Context

This replaces `~/.agents/context/fantasy-waiver-sweep.md` and
`~/.agents/context/fantasy-start-sit.md` for the snapshot.

- Sleeper user: `owner_id` `me`
- Leagues:

  | Short name | League | Rosters | Matchups | Scoring |
  |---|---|---|---|---|
  | OFFICE | `league-office.json` | `rosters-office.json` | `matchups-office.json` | half PPR, 12 teams, 1 FLEX, K |
  | FAMILY | `league-family.json` | `rosters-family.json` | `matchups-family.json` | full PPR, 10 teams, 3 FLEX, no K |

- Break ties by playoff schedule from Week 11 on in both leagues.

## Files

| File | Stands in for |
|---|---|
| `state.json` | Sleeper `/state/nfl` |
| `league-*.json` | Sleeper `/league/<id>` |
| `rosters-*.json` | Sleeper `/league/<id>/rosters` |
| `matchups-*.json` | Sleeper `/league/<id>/matchups/10`, the lineups as saved |
| `players.json` | Sleeper `/players/nfl`, cut to players with a team or a roster spot |
| `snap_counts_2026.csv` | nflverse snap counts, offense only, weeks 1 to 9 |
| `stats_player_week_2026.csv` | nflverse weekly player stats, offense only, weeks 1 to 9 |
| `games.csv` | nflverse schedule, kickoff times (ET), lines and expected QBs for 2026 |
| `news.md` | injury and depth chart news as of the snapshot |
