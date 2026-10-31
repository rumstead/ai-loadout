---
name: fantasy-waiver-sweep
description: Weekly fantasy football waiver sweep for Sleeper leagues. Audits the bench, finds role-change pickups that could be league winners (not just trending adds), checks positional depth against upcoming byes, prices each claim from the league's waiver settings, and names at most one add/drop per league plus any DEF, K or QB streamer. Use when the user asks to run the waiver sweep, audit their bench, find league winners, decide who to drop for a pickup, or what to claim on waivers in a Sleeper league.
license: MIT
compatibility: Needs a shell with curl and Python, network access to api.sleeper.app, github.com and raw.githubusercontent.com, and web search. Sleeper leagues only.
---

# Fantasy Waiver Sweep

Find the add that could win a league before everyone else notices, without hollowing out the bench. Trending adds and platform projections are never the reason for a move.

## Context

If `~/.agents/context/fantasy-waiver-sweep.md` exists, read it first. It names the user's Sleeper account and leagues, and anything in it overrides the defaults below. Otherwise take the Sleeper username or user ID from the conversation or memory, and ask for it if neither has one. `context.example.md` shows the fields.

## Data

Fetch everything with `curl` (`-L` for GitHub), save it to disk, and analyze it with Python. Don't print the big files. Never guess the week.

- **Sleeper public API** (`https://api.sleeper.app/v1`):
  - `/state/nfl`: `season` and `week`.
  - `/user/<username>`: `user_id`, when you only have a username.
  - `/user/<user_id>/leagues/nfl/<season>`: the user's leagues. Use the ones the context lists, or all of them.
  - `/league/<id>`: settings, below.
  - `/league/<id>/rosters`: rosters, IR (`reserve`), and per roster `settings.waiver_budget_used` and `settings.waiver_position`. The user's roster is the one whose `owner_id` or `co_owners` has their `user_id`.
  - `/players/nfl`: injury status and depth chart. It is large, fetch it once.
  - A player or team DEF is available if it is on no roster in that league.
- **nflverse**, the main usage source: `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_<season>.csv` and `https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_<season>.csv`.
- **Schedule, byes and Vegas lines**: `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv`. A team is on bye in a week it has no game. `spread_line` is from the home team's side: home implied total = `total_line`/2 + `spread_line`/2, away = `total_line`/2 - `spread_line`/2. The `roof` and `wind` columns cover weather, and `home_qb_name` and `away_qb_name` show the expected starting QBs.
- **News** (web search and fetch): injuries, practice reports, depth-chart moves.

Read each league's format from `/league/<id>`:

| Field | Meaning |
|---|---|
| `total_rosters` | league size |
| `roster_positions` | starting slots, whether there is a K or DEF slot, and bench size (`BN` count) |
| `scoring_settings.rec` | 1 is full PPR, 0.5 half, 0 standard |
| `settings.type` | 0 redraft, 1 keeper, 2 dynasty. `max_keepers` can be nonzero in a redraft league, ignore it |
| `settings.waiver_type` | 2 FAAB, 0 rolling priority, 1 reverse standings |
| `settings.waiver_budget`, `settings.waiver_bid_min` | FAAB budget and minimum bid. Remaining budget is `waiver_budget` minus the roster's `waiver_budget_used` |
| `settings.playoff_week_start` | first playoff week |

In a keeper or dynasty league, weigh next season too: a young player with a growing role is worth more than this week's points suggest.

## Process

1. **Bench audit.** For each bench player, check the snap and touch trend over the last 2 to 3 games, any path to more work, and health. A player is droppable only if his role shrank two straight weeks, he's buried with no path to more work, or he's injured with no timeline.
2. **Depth vs. byes.** Over the next 3 weeks, flag any position with no healthy backup. When choosing a drop, positional balance beats individual player value.
3. **Candidates.** Screen nflverse for available players with a +20-point snap jump or rising targets or carries, then check the news for starters lost to injury. Strength of signal: starter out for the season, then a snap jump, then next man up behind a fragile starter.
4. **Decide.** Add only if the candidate clearly beats the weakest bench spot. "No move" is fine.
5. **Price it.**
   - FAAB: 1 to 5% of the budget for a stash, 30 to 50% only for a lead-role takeover. Never bid below `waiver_bid_min`.
   - Rolling priority or reverse standings: spend priority only on a lead-role takeover, otherwise wait for free agency.
   - Within four weeks of `playoff_week_start`, break ties by playoff schedule.
6. **Streamers.** Check DEF every week in leagues with a DEF slot, and K in leagues with a K slot. Check QB only when the user's starter is hurt or on bye. Compare the starter's upcoming matchup with the best available option.
   - **DEF:** a lower opponent implied total is better, plus the opposing QB's sacks and interceptions per game from nflverse. Injuries carry the most weight. Check the opposing offense for a backup QB starting (`games.csv` QB names plus the news), missing offensive linemen, and a missing WR1 or RB1. Check the user's own defense for missing pass rushers and corners. A backup QB start clears the bar even with a smaller implied-total gap.
   - **K:** a higher team implied total is better, plus a dome or low wind. Downgrade a kicker whose own QB or top receiver is out.
   - **QB:** when streaming, look for an opposing defense missing its top pass rusher or corners.
   - Recommend a swap only for a clear gap, roughly 4 or more points of implied total or a major injury edge. The swap is one for one (drop the current DEF, K or QB). Streamers are contested, so treat them as real claims. FAAB: bid 1 to 3% of the budget. Rolling priority: a claim drops the user to last, so claim a streamer only when there's no bigger claim that week and the gap is large. Otherwise name the best option likely to reach free agency.

## Output

The reader is on a phone and should get the answer in 30 seconds. Use plain text and this exact shape. The example shows the format only, with players from a past week and made-up league names. Each league goes by its short name from the context, or its Sleeper name in capitals.

```
Subject: Waiver sweep Wk 8: add Jaydon Blue (both leagues)

OFFICE: Add Jaydon Blue (RB, PHI), drop TreVeyon Henderson. Bid $30 of $74.
- Barkley (back) is tracking to miss Sunday, and Blue is the Eagles' only healthy RB.
- Henderson has played 16 to 24% of snaps three weeks running.
- Risk: if Barkley plays, Blue is a $30 handcuff.
- Week 10: no TE when Loveland is on bye.
STREAM: DEF Jaguars over Bengals, bid $2 (Colts start a backup QB; implied 17 vs 26).

FAMILY: Add Jaydon Blue (RB, PHI), drop Jalen Coker. Use priority #2.
- A lead RB beats your ninth WR in full PPR.
- Coker's targets fell from 13 to 4.
- Risk: Coker had 26 to 37% target shares when healthy.

WATCH: Breece Hall (quad, week to week), Dylan Sampson (CLE, Judkins handcuff).

Sources: bleedinggreennation.com/..., pff.com/...
```

Rules:
- The subject line carries the headline move.
- Each league gets one headline line, then at most 4 bullets. Each bullet is one sentence, with at most one number.
- Always include exactly one `Risk:` bullet. Add a `Week N:` bullet only for a real depth gap.
- Add one `STREAM:` line per league only when a DEF, K or QB swap clears the bar, with the claim price, the key injury if there is one, and the implied totals.
- With no move, the headline is `OFFICE: No move.` plus one bullet saying why.
- No headings, numbered sections, banners, nested lists or bench rankings.
- At most 3 sources, and only news articles (full URLs). Never list API or data URLs.
- Mention a data problem (stale nflverse week, blocked site) only if it changed a call, in one line at the end.
- Never make roster moves. If Sleeper is unreachable, say so in two lines naming the host that failed.
