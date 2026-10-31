---
name: fantasy-start-sit
description: Evaluate fantasy football start/sit, waiver, and streaming decisions from a lineup, matchup, roster, or free-agent screenshot, using independent analysis (Vegas lines, snap and target usage, rushing floor, injury news, weather, defensive matchups) rather than the platform's projections. Use this skill whenever the user shares a fantasy lineup, matchup, roster, or player-list image, or asks who to start, who to sit, what to do at flex, whether to swap someone, whether to pick up or stream a player, how their matchup looks, or for help setting a lineup. Trigger even when they don't say the words "start" or "sit". A screenshot of a fantasy matchup or free-agent list with any question attached is enough, as is "run the same analysis for this team" or "check my lineup."
license: MIT
compatibility: Works from a screenshot on any fantasy platform. Needs web search, and a shell with curl for the Sleeper and nflverse data.
---

# Fantasy Start/Sit Evaluation

Set a lineup by finding the decisions that are still live, researching only those with independent evidence, and choosing based on whether the manager needs floor or ceiling.

Two failure modes this skill exists to prevent:

1. **A generic player-by-player writeup** that burns the user's attention on slots they can't change. Most lineups are already 90% correct. The value is in the one or two genuinely contested slots.
2. **Laundering the platform's projections.** Fantasy apps are good at running leagues and bad at projecting players. Their numbers update slowly, miss role changes, and anchor on last season. Repeating them back as the reason for a decision adds nothing the user can't see on their own screen. Build the case from primary evidence instead.

## Context

If `~/.agents/context/fantasy-start-sit.md` exists, read it first. It can list the user's leagues with their scoring formats and team names, and style rules for the response. Anything in it overrides the defaults below. `context.example.md` shows the fields.

## Step 0: Confirm scoring format

If the context gives the format for the league in the screenshot, use it and skip this step. Otherwise ask before researching, in one short question. PPR, half-PPR, and standard change receiver and pass-catching-back value enough to flip a flex call. If the user already told you the format earlier in the conversation, don't ask again.

Ask only this. Don't stack on questions about league size, roster settings, or record. Infer those from the screenshot.

## Step 1: Parse the lineup

Read the image carefully and build a mental table before touching any tools.

- **Which side is the user's?** Usually left, and usually the one whose team name or handle the user has referenced or the context lists. If genuinely ambiguous, check which side's already-scored players sum to the score shown on that side.
- **Every starter**: name, position, slot type (a WR in a W/R/T slot is a flex, not a WR slot), NFL team, opponent, kickoff time, and game status.
- **Every bench player**, same fields. The bench is what makes a slot a decision.
- **IR / OUT / doubtful** players, which are non-options.
- **Actual scores** for games already played, and how many players each side has left.

Note the app's projections only so you can recognize them later. Do not use them to rank players or classify slots.

Then classify each starting slot:

- **Locked**: the player's game is final or in progress. Nothing to decide. Mention only in one line if a result changes the floor/ceiling calculus.
- **Not a decision**: the bench holds no eligible alternative (single QB, one kicker, one defense). Say so briefly.
- **Live**: an eligible bench alternative exists. These are the only slots worth research.

Usually there are one to three live slots. That's the whole job.

## Step 2: Establish the slate

Get the week from `https://api.sleeper.app/v1/state/nfl` and the week's games, kickoff times, and Vegas lines from `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv` (`curl -L`, then filter with Python). If the harness has a live sports data tool, use it for game statuses and in-progress scores; otherwise search for them. Don't infer the week from memory; screenshots of past and future weeks look identical.

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

## Waiver and pickup questions

When the user shares a free-agent list or asks whether to add a player (including "should I bench X for a waiver pickup"), run the same Step 4 evidence on the incumbent and the top two or three real alternatives. Ignore the list's projection sort order. Also weigh:

- **Waiver timing**: a player still on waivers may not clear before his game.
- **Roster cost**: name the player who would be dropped.
- **Durability of the role**: a one-week streamer is fine if the user has a droppable body; a fill-in QB whose starter may return is not worth a real asset.

## Drop recommendations

Suggesting a drop is a higher bar than suggesting a start. A bad start costs one week; a bad drop can cost a season. Before naming anyone as droppable:

- **Only suggest a drop when a real roster need exists.** If the user didn't ask about an add, don't volunteer a drop list.
- **Use current-season usage, never preseason takes.** Check actual snap share, route participation, carries, and targets from games played. A summer article calling someone a "third-down back" is not evidence once real snap counts exist.
- **Separate snaps from touches.** A back who splits snaps but trails in touches is still one injury away from a full role. That is a hold.
- **Default to holding early in the season.** Through roughly Week 4, sample sizes are tiny. Prefer dropping players with a clear negative signal: injured and inactive, buried in a committee with no path to more work, or a role that just disappeared.
- **Rank the whole bench before naming one.** Compare every bench player on role, path to more work, and health. Name only the clear bottom of that list, with the evidence.
- **Weigh contingency value.** Handcuffs and backs in near-even splits carry value beyond their weekly points.

## Output format

Keep it to a verdict plus three to four bullets. The user is on a phone.

```
**Verdict: [start X over Y / no changes needed].** [One sentence of why.]

- **[The contested slot]**: the call and the two or three pieces of evidence behind it (usage, implied total, floor), including the strongest counterargument.
- **[Second contested slot, if any]**: same.
- **[Confirmations]**: one bullet covering every other live slot that checks out, with the single relevant fact each. Note which slots aren't decisions at all.
- **[What to watch]**: the biggest risk, and any game-time decision that needs a second look before kickoff.

**Waivers:** [1-2 pickups or streamers that would fix a weak slot, with the usage or environment evidence.]
**Opponent:** [1-2 weak spots in their lineup: questionable starters, fill-in roles, low implied totals, locked low scores.]
```

Skip any section that has nothing real in it.

## Guidelines that keep the advice honest

**Never suggest changing a locked player.** If the game is final or underway, the slot is closed.

**Say "no changes" when that's the answer.** Inventing a swap to seem useful costs the user points.

**Give the counterargument.** Every close call has one.

**Cite the specific number, and make it a real one.** "Brooks played 38 snaps to Lloyd's 30 and ran 20 pass-pro reps" or "Minnesota's implied total is 21.5 as a 5.5-point underdog" is useful. "Projected for 11.6" is not.

**Handle game-time decisions explicitly.** If a player is a true coin flip, name the fallback and when the news should land. Flag Thursday players whose slot must be set before kickoff.

**Don't pad with locked players.**

## Worked example

A manager shares a matchup with a flex decision between a running back and a slot receiver in full PPR. The app projects the back higher. Research shows the back lost the snap lead to a teammate who handles pass protection, caught zero passes on one target, and runs behind a line ranked 25th in run-block win rate. The receiver tied for second on his team in targets and works the short areas of the field in one of the league's highest-scoring offenses.

The verdict starts the receiver for floor, names the back's positive game script as the counterargument, and flags that the receiver plays Thursday so the change must be made before kickoff. The app's projection never appears as a reason.

## Other sports

The same structure works for other fantasy sports. Swap the weather step for whatever drives that sport's variance (rest days and back-to-backs in basketball, starting pitcher confirmation and park factors in baseball, goalie confirmation in hockey) and use betting lines and usage data over platform projections the same way.
