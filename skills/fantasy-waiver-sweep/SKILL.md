---
name: fantasy-waiver-sweep
description: Weekly fantasy football waiver sweep for Sleeper leagues. Sets next week's lineup first and fills any hole a bye or injury leaves, then audits the bench, finds role-change pickups that could be league winners (not just trending adds), checks positional depth against upcoming byes, prices each claim from the league's waiver settings, and gives a DEF and K verdict every week. Names at most one add/drop per league plus any DEF, K or QB stream. Use when the user asks to run the waiver sweep, audit their bench, find league winners, decide who to drop for a pickup, or what to claim on waivers in a Sleeper league.
license: MIT
compatibility: Needs a shell with curl and Python, network access to api.sleeper.app, github.com and raw.githubusercontent.com, and web search. Sleeper leagues only.
metadata:
  version: "0.2.0" # x-release-please-version
---

# Fantasy Waiver Sweep

Fill next week's lineup first, then find the add that could win a league before everyone else notices, without hollowing out the bench. Trending adds and platform projections are never the reason for a move.

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
- **nflverse**, the main usage source: `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_<season>.csv` and `https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_<season>.csv`. Match players by name and team, and note that nflverse writes the Rams as `LA` where Sleeper writes `LAR`.
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
| `settings.reserve_slots`, `settings.reserve_allow_out`, `settings.reserve_allow_doubtful` | IR slots, and whether Out or Doubtful players may use them |
| `settings.playoff_week_start` | first playoff week |

In a keeper or dynasty league, weigh next season too: a young player with a growing role is worth more than this week's points suggest.

## Process

1. **Next week's lineup.** Fill every starting slot with the user's best healthy players who aren't on bye. A slot left empty, or filled only by a player who is Out, is a hole. Before dropping anyone, move each Out player to an open IR slot the league allows, which opens a roster spot for free. A hole fill is the league's one add for the week and the headline, ahead of any upside add.
2. **Bench audit.** For each bench player, check the snap and touch trend over the last 2 to 3 games, any path to more work, and health. A player is droppable only if his role shrank two straight weeks, he's buried with no path to more work, or he's injured with no timeline. The backup to a lead back is not buried: the starter's injury is his path, and that upside is what an add has to beat.
3. **Depth vs. byes.** Over the next 3 weeks, flag any position with no healthy backup.
4. **Candidates.** Screen nflverse for available players with a +20-point snap jump or rising targets or carries, then check the news for starters lost to injury. Strength of signal: starter out for the season, then a snap jump, then next man up behind a fragile starter. For a hole, line up the top three available players at that position and compare their fantasy points per game over their last 4 games in the league's scoring, their team's implied total, and their health, including the QB throwing to them. Snap share breaks ties and never outranks points.
5. **Decide.** Add only if the candidate clearly beats the weakest bench spot. Positional balance beats player value: never drop from a thin position to add to a deep one, and a swap within a position (an RB for an RB) needs a lead-role takeover. "No move" is fine.
6. **Price it.**
   - FAAB: 1 to 3% of the budget for a one-week hole fill, 1 to 5% for a stash, 30 to 50% only for a lead-role takeover. Never bid below `waiver_bid_min`.
   - Rolling priority or reverse standings: spend priority only on a lead-role takeover or a hole no free agent can fill, otherwise wait for free agency.
   - Within four weeks of `playoff_week_start`, break ties by playoff schedule.
7. **DEF, K and QB.** Give a DEF verdict every week in leagues with a DEF slot and a K verdict in leagues with a K slot, even when the answer is to keep the starter. Check QB only when the user's starter is hurt or on bye. Compare the starter's upcoming matchup with the best available option.
   - **DEF:** a lower opponent implied total is better, plus the opposing offense's sacks allowed and giveaways per game this season. Compute both for the current DEF's opponent and each candidate's from `stats_player_week`, summed over the offense's players and divided by its games played: sacks allowed is `sacks_suffered`, and giveaways are `passing_interceptions` plus every `*_fumbles_lost` column. Injuries carry the most weight. Check the opposing offense for a backup QB starting (`games.csv` QB names plus the news), missing offensive linemen, and a missing WR1 or RB1. Check the user's own defense for missing pass rushers and corners. A backup QB start clears the bar even with a smaller implied-total gap.
   - **K:** a higher team implied total is better, plus a dome or low wind. Downgrade a kicker whose own QB or top receiver is out.
   - **QB:** when streaming, look for an opposing defense missing its top pass rusher or corners.
   - Recommend a swap only for a clear gap, roughly 4 or more points of implied total, a major injury edge, or a giveaway rate at least double the current opponent's. The swap is one for one (drop the current DEF, K or QB). FAAB: bid 1 to 3% of the budget. Rolling priority or reverse standings: never spend priority on a DEF or K stream, and on a QB stream only when the starter is out for more than one week. Waivers clear before the week's games, so the stream is a free agent pickup once waivers clear, with the next-best option named in case someone claims it.

## Output

The reader is on a phone and should get the answer in 30 seconds. Use plain text and this exact shape. The example shows the format only, with players from a past week and made-up league names. Each league goes by its short name from the context, or its Sleeper name in capitals.

```
Subject: Waiver sweep Wk 8: add Jaydon Blue (OFFICE), Mason Taylor for the TE hole (FAMILY)

OFFICE: Add Jaydon Blue (RB, PHI) over Tyjae Spears, drop TreVeyon Henderson. Bid $30 of $74.
- Barkley (back) is tracking to miss Sunday, and Blue is the Eagles' only healthy RB.
- Spears splits the Titans' work with Pollard.
- Henderson has played 16 to 24% of snaps three weeks running.
- Risk: if Barkley plays, Blue is a $30 handcuff.
DEF: Stream Jaguars over Bengals, bid $2 (Colts start a backup QB; implied 17 vs 26; giveaways 1.8 vs 0.9 a game).
K: Keep Bass (Bills implied 27, best available 23).

FAMILY: Add Mason Taylor (TE, NYJ) over Zach Ertz, Hunter Henry to IR, no drop. Use priority #2.
- Kittle is on bye and Taylor has averaged 9 points over his last four games.
- Ertz plays more snaps but his QB is a backup this week.
- Risk: Taylor's targets dipped to 2 last week.
- Week 10: no healthy RB backup when Swift is on bye.
DEF: Keep Steelers (Browns implied 17 with 1.6 giveaways a game, no free agent better on either).

WATCH: Breece Hall (quad, week to week), Dylan Sampson (CLE, Judkins handcuff).

Sources: bleedinggreennation.com/..., pff.com/...

MOVES
| League | Move | Player | Price |
|---|---|---|---|
| OFFICE | Add | Jaydon Blue (RB, PHI) | $30 |
| OFFICE | Drop | TreVeyon Henderson (RB, NE) | |
| OFFICE | Add | Jaguars (DEF) | $2 |
| OFFICE | Drop | Bengals (DEF) | |
| FAMILY | IR | Hunter Henry (TE, NE) | |
| FAMILY | Add | Mason Taylor (TE, NYJ) | priority #2 |
```

Rules:
- The subject line carries the headline move.
- Each league gets one headline line, then at most 4 bullets. Each bullet is one sentence, with at most one number.
- A lineup hole is the headline: add the fill and name any IR move in the same line.
- An `Add` headline names the runner-up with `over`: the best option the pick beat for the same spot.
- Always include exactly one `Risk:` bullet. Add a `Week N:` bullet only for a depth gap in a later week.
- Every league gets one `DEF:` line if it has a DEF slot and one `K:` line if it has a K slot: `Keep <current> (<why, with implied totals>)` or `Stream <new> over <current>, <price> (<why, with implied totals>)`, where the price in a rolling-priority league is `free agency after waivers clear`. A DEF line also gives both opponents' giveaways per game (interceptions plus fumbles lost, not sacks). Add a `QB:` line in the same shape only when the starter is hurt or on bye.
- With only IR moves, the headline is `FAMILY: No add. <players> to IR.` With no move at all, it is `OFFICE: No move.` Either way, add one bullet saying why there's no add.
- End with `MOVES` and a table of every roster move from the lines above, one row each for an IR move, add or drop, in the order to make them. Leave out keeps and WATCH players. With no moves in any league, write `MOVES: none.` instead.
- No headings, numbered sections, banners, nested lists or bench rankings.
- At most 3 sources, and only news articles (full URLs). Never list API or data URLs. Sources go just before `MOVES`.
- Mention a data problem (stale nflverse week, blocked site) only if it changed a call, in one line just before Sources.
- Never make roster moves. If Sleeper is unreachable, say so in two lines naming the host that failed.
