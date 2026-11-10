---
name: fantasy-start-sit
description: Evaluate fantasy football start/sit decisions from a lineup, matchup, or roster screenshot, or straight from a Sleeper league, using independent analysis (Vegas lines, snap and target usage, rushing floor, injury news, weather, defensive matchups) rather than the platform's projections. Use this skill whenever the user shares a fantasy lineup, matchup, roster, or player-list image, or asks who to start, who to sit, what to do at flex, whether to swap someone, whether a free agent or streamer should start over someone this week, how their matchup looks, or for help setting a lineup. Trigger even when they don't say the words "start" or "sit", as with "check my lineup." Waiver claims, bids, and drops in a Sleeper league belong to fantasy-waiver-sweep. When a request asks for both, run that sweep first, then this skill on the lineup.
license: MIT
compatibility: Works from a screenshot on any fantasy platform, or from a Sleeper league without one. Needs web search, and a shell with curl and Python for the Sleeper and nflverse data.
metadata:
  version: "0.1.0" # x-release-please-version
---

# Fantasy Start/Sit Evaluation

Set a lineup by finding the decisions that are still live, researching only those with independent evidence, and choosing based on whether the manager needs floor or ceiling.

Two failure modes this skill exists to prevent:

1. **A generic player-by-player writeup** that burns the user's attention on slots they can't change. Most lineups are already 90% correct. The value is in the one or two genuinely contested slots.
2. **Laundering the platform's projections.** Fantasy apps are good at running leagues and bad at projecting players. Their numbers update slowly, miss role changes, and anchor on last season. Repeating them back as the reason for a decision adds nothing the user can't see on their own screen. Build the case from primary evidence instead.

## Waivers in the same request

If the request also asks about waivers, claims or pickups for a Sleeper league ("start sit waivers", "set my lineup and run waivers"), and `fantasy-waiver-sweep` hasn't run yet in this conversation, invoke the `fantasy-waiver-sweep` skill now, before Step 0, and finish it. Then come back here for the lineup. Its adds count as bench options, and its holes are already filled. Don't price claims or pick drops yourself in that case.

## Context

If `~/.agents/context/fantasy-start-sit.md` exists, read it first. It can list the user's leagues with their scoring formats and team names, and style rules for the response. Anything in it overrides the defaults below. `context.example.md` shows the fields.

## Data

`scripts/sleeper_data.py` (Python standard library, `--help` for usage) does the fetching and summaries in Steps 1 to 4: `fetch` saves the Sleeper and nflverse files, `lineup` lists both teams in a Sleeper matchup with each player's opponent, kickoff, injury status and byes, `lines` gives the week's kickoffs, implied totals and weather, `usage` gives weekly snaps, touches and points for named players, and `free-agents` ranks available players. Use it rather than writing your own matching: it ties nflverse rows to Sleeper players by `gsis_id`, then full name with suffix plus team, and never by name alone against an inactive player, so a retired namesake can't pass for a starter.

## Step 0: Confirm scoring format

If the context gives the format for the league, or it's a Sleeper league (`scoring_settings.rec` is 1 for full PPR, 0.5 for half, 0 for standard), use it and skip this step. Otherwise ask before researching, in one short question. PPR, half-PPR, and standard change receiver and pass-catching-back value enough to flip a flex call. If the user already told you the format earlier in the conversation, don't ask again.

Ask only this. Don't stack on questions about league size, roster settings, or record. Infer those from the screenshot.

## Step 1: Parse the lineup

Read the image carefully and build a mental table before touching any tools. Without an image, for a Sleeper league, run `fetch` and then `lineup` for each league. Both need IDs: take the Sleeper user ID and league IDs from the context, or look them up from a username with `https://api.sleeper.app/v1/user/<username>` (its `user_id` is `lineup --owner`) and `https://api.sleeper.app/v1/user/<user_id>/leagues/nfl/<season>`, and ask for the username if neither the context nor the conversation has it.

- **Which side is the user's?** Usually left, and usually the one whose team name or handle the user has referenced or the context lists. If genuinely ambiguous, check which side's already-scored players sum to the score shown on that side.
- **Every starter**: name, position, slot type (a WR in a W/R/T slot is a flex, not a WR slot), NFL team, opponent, kickoff time, and game status.
- **Every bench player**, same fields. The bench is what makes a slot a decision.
- **IR / OUT / doubtful** players, which are non-options.
- **Actual scores** for games already played, and how many players each side has left.

Note the app's projections only so you can recognize them later. Do not use them to rank players or classify slots.

Then classify each starting slot:

- **Hole**: the starter is on bye or Out. This must change. Fill it from the bench first, and only when nothing eligible is on the bench, look at free agents (see Free-agent starts).
- **Locked**: the player's game is final or in progress. Nothing to decide. Mention only in one line if a result changes the floor/ceiling calculus.
- **Not a decision**: the bench holds no eligible alternative (single QB, one kicker, one defense). Say so briefly.
- **Live**: an eligible bench alternative exists. These are the only slots worth research.

Usually there are one to three live slots, plus any holes. That's the whole job.

## Step 2: Establish the slate

Get the week from `https://api.sleeper.app/v1/state/nfl` and the week's games, kickoff times, and Vegas lines from `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv` (the script's `lines` command reads both). If the harness has a live sports data tool, use it for game statuses and in-progress scores; otherwise search for them. Don't infer the week from memory; screenshots of past and future weeks look identical.

Note the kickoff of every player in a hole or live slot and of each bench option. Sleeper and most platforms lock each player at his own game's kickoff, so a swap has to be made before the earlier of the two players' kickoffs. Flag anything before Sunday 1:00 PM ET: Thursday and Saturday games, and the 9:30 AM ET international games.

## Step 3: Pull league-wide context once

Do these before player-specific research so you don't repeat them per player.

1. **Vegas lines for the week.** Spread and total for every relevant game, from `spread_line` and `total_line` in `games.csv`. `spread_line` is from the home team's side: home implied total = `total_line`/2 + `spread_line`/2, away = `total_line`/2 - `spread_line`/2. Search for the current line when a big injury may have moved it since. Betting markets aggregate far more information than fantasy app projections and are the best single signal for scoring environment and game script.
2. **Official injury report** for the current week.
3. **Same-day injury updates.** The Wednesday-Friday report is stale by Sunday. Look for pregame "injuries to monitor" roundups or beat-reporter updates. Roster moves are tells: a team elevating practice-squad receivers is preparing to sit someone.
4. **Weather.** The `roof` and `wind` columns in `games.csv` first, then a forecast for open-air games. Wind above roughly 15 mph (deep passing, kickers), sustained rain, extreme heat. Domes and retractable roofs are non-factors; state that rather than analyzing.

## Step 4: Build an independent case for each live slot

For each contested slot, research the specific players. The evidence hierarchy, strongest first:

1. **Role and usage.** From nflverse (`https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_<season>.csv` and `.../stats_player/stats_player_week_<season>.csv`) where it covers the stat. Snap share, route participation, target share, carry share, red-zone and goal-line work, pass-protection snaps for backs. Who is splitting work and why. This matters more than matchup.
2. **Job security.** Is the player a fill-in (backup QB until a starter clears protocol, RB1 only while someone is suspended)? A role that can vanish midweek is a real risk.
3. **Game environment.** Implied team total and expected script. Heavy favorites run late; heavy underdogs throw. A pass-catching back or slot receiver gains value as an underdog; a between-the-tackles back loses it.
4. **Position-specific floor.** For QBs, rushing production is the floor. For PPR receivers and backs, target volume is the floor. Touchdown-dependent profiles have no floor.
5. **The matchup.** Opposing defense's recent performance and personnel (injured corners, safeties, pass rushers, run-block win rate for the offensive line). Weight current-season evidence and personnel changes over last season's rankings.
6. **Recent news** that changes any of the above: a play-caller change, a teammate returning or going down, a snap-count limitation.

**Platform projections are not evidence.** Don't cite them as a reason, don't use a projection gap to break a tie, and don't present them as the answer. If the app's number strongly disagrees with your conclusion, say briefly why your evidence points the other way.

## Step 5: Decide floor or ceiling

Read the margin from real information, not the app's projected totals:

- **Games in progress or finished**: use actual scores and players remaining.
- **Before kickoff**: compare both lineups yourself. Count questionable starters, fill-in roles, players in low implied-total games, and players with no floor. Call the matchup favored, close, or unfavored, and say what drove that read.

Then:

- **Unfavored or behind** → chase ceiling. Prefer big-play profiles, workhorse backs, volatile players in high-total games.
- **Favored or ahead** → protect floor. Prefer role certainty and predictable volume over upside swings.
- **Fewer players left than the opponent** → each remaining starter carries more weight. Lean ceiling even with a small lead.
- **Genuinely close** → say so, and let role certainty decide.

State which mode you're in and why.

## Free-agent starts

This skill decides who starts this week. Waiver claims, FAAB bids, bench audits, and drops in a Sleeper league belong to `fantasy-waiver-sweep` (see Waivers in the same request).

Look at free agents only for a hole the bench can't fill, or when the user asks whether a specific free agent or streamer should start over a rostered player. Run the same Step 4 evidence on the incumbent and the top two or three real alternatives (the script's `free-agents` command screens a Sleeper league), and ignore the list's projection sort order. Also weigh:

- **Waiver timing**: a player still on waivers may not clear before his game.
- **Roster cost**: use an open bench spot or an Out player moved to an open IR slot before any drop.
- **Durability of the role**: a one-week streamer is fine if the user has a droppable body; a fill-in QB whose starter may return is not worth a real asset.

**Drops.** A DEF, K or QB stream is one for one, so it drops the player it replaces. Any other drop in a Sleeper league is the sweep's call. On another platform, name one only when the user asked about an add, and only a player whose role shrank two straight weeks, who is buried with no path to more work, or who is injured with no timeline. Judge that from current-season snaps and touches, never preseason takes, and hold the backup to a lead back: the starter's injury is his path to the job.

## Output format

Keep it to a verdict plus three to four bullets per league, then one table of moves. The user is on a phone.

```
**[League]: [start X over Y / no changes needed].** [One sentence of why.]

- **[The contested slot or hole]**: the call and the two or three pieces of evidence behind it (usage, implied total, floor), including the strongest counterargument.
- **[Second contested slot, if any]**: same.
- **[Confirmations]**: one bullet covering every other live slot that checks out, with the single relevant fact each. Note which slots aren't decisions at all.
- **[What to watch]**: the biggest risk, and any game-time decision that needs a second look before kickoff.

**Free agents:** [only for a hole the bench can't fill or a free agent the user asked about, with the usage or environment evidence.]
**Opponent:** [1-2 weak spots in their lineup: questionable starters, fill-in roles, low implied totals, locked low scores.]

MOVES
| League | Move | Player | Price | By |
|---|---|---|---|---|
| WORK | Start | Jauan Jennings (WR, SF) at FLEX | | Thu 8:15 PM ET |
| WORK | Bench | Jakobi Meyers (WR, JAX) | | Thu 8:15 PM ET |
| WORK | Add | Tyler Higbee (TE, LAR) | $2 | Wed waivers |
| WORK | Start | Tyler Higbee (TE, LAR) at TE | | Sun 4:05 PM ET |
| WORK | Bench | Sam LaPorta (TE, DET) | | Sun 4:05 PM ET |
```

The rows show the format only, with players from a past week and a made-up league name.

- Skip any bullet or line that has nothing real in it. With more than one league, repeat the block per league and write one `MOVES` table at the end.
- `MOVES` lists every change the user has to make, in the order to make them, one player per row: a `Start` row and a `Bench` row for each swap, plus `Add` and `Drop` rows for a free-agent start. A `Start` row's player always ends with ` at <slot>`, as in `Jauan Jennings (WR, SF) at FLEX`. `League` is the short name from the context, or the league's name in capitals.
- `By` is the deadline. A `Start` or `Bench` row is the earlier kickoff of the two players in that swap, the one going in and the one coming out, as day, time and ET. Other players in the lineup don't count. A player on bye has no kickoff, so his swap is due by the other player's. An IR move is `now`. A claim and its drop are the league's next waiver run (`Wed waivers` on Sleeper's default), or `now` for a free agent who has cleared waivers.
- `Price` stays empty for lineup rows and holds the bid or waiver priority for an add.
- With no changes in any league, write `MOVES: none.` instead of the table.
- When `fantasy-waiver-sweep` ran for the same request, write one `MOVES` table for both and leave out the sweep's own table: the sweep's IR, Add and Drop rows first, then the lineup rows. Where both name a swap for the same slot, keep this skill's rows and drop the sweep's.

## Guidelines that keep the advice honest

**Never suggest changing a locked player.** If the game is final or underway, the slot is closed.

**Say "no changes" when that's the answer.** Inventing a swap to seem useful costs the user points.

**Give the counterargument.** Every close call has one.

**Cite the specific number, and make it a real one.** "Brooks played 38 snaps to Lloyd's 30 and ran 20 pass-pro reps" or "Minnesota's implied total is 21.5 as a 5.5-point underdog" is useful. "Projected for 11.6" is not.

**Handle game-time decisions explicitly.** If a player is a true coin flip, name the fallback and when the news should land. Flag any swap due before Sunday 1:00 PM ET (Thursday, Saturday, or a 9:30 AM ET international game).

**Don't pad with locked players.**

## Worked example

A manager shares a matchup with a flex decision between a running back and a slot receiver in full PPR. The app projects the back higher. Research shows the back lost the snap lead to a teammate who handles pass protection, caught zero passes on one target, and runs behind a line ranked 25th in run-block win rate. The receiver tied for second on his team in targets and works the short areas of the field in one of the league's highest-scoring offenses.

The verdict starts the receiver for floor, names the back's positive game script as the counterargument, and flags that the receiver plays Thursday so the change must be made before kickoff. The app's projection never appears as a reason.

## Other sports

The same structure works for other fantasy sports. Swap the weather step for whatever drives that sport's variance (rest days and back-to-backs in basketball, starting pitcher confirmation and park factors in baseball, goalie confirmation in hockey) and use betting lines and usage data over platform projections the same way.
