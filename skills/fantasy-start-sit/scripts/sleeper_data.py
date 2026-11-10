#!/usr/bin/env python3
"""Fetch and summarize Sleeper and nflverse data for the fantasy skills.

The canonical copy lives in shared/fantasy/ of the ai-loadout repo, and
shared/sync.sh copies it into each fantasy skill's scripts/ folder so every
skill ships with it. Edit the canonical copy, then run shared/sync.sh.

Standard library only. Every command but fetch reads local files, so it runs
the same against a live fetch or a saved snapshot.

    sleeper_data.py fetch --out DIR --league ID [--league ID ...]
    sleeper_data.py lines --games games.csv --season 2026 --week 10
    sleeper_data.py lineup --league L.json --rosters R.json --matchups M.json \\
        --players players.json --games games.csv --week 10 --owner USER_ID
    sleeper_data.py usage --stats S.csv --snaps N.csv --players players.json \\
        --rec 0.5 --name "Breece Hall" [--name ...] [--since 5]
    sleeper_data.py free-agents --stats S.csv --snaps N.csv --players players.json \\
        --rosters R.json --games games.csv --season 2026 --week 10 --rec 1
    sleeper_data.py offense --stats S.csv --team NYJ [--team ...]
"""

import argparse
import csv
import datetime
import json
import os
import re
import sys
import urllib.request

SLEEPER = "https://api.sleeper.app/v1"
NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
GAMES_CSV = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"

# nflverse team codes that differ from Sleeper's.
TEAM_ALIASES = {"LA": "LAR"}
SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
SKILL_POSITIONS = ("QB", "RB", "WR", "TE")
UNAVAILABLE = {"Out", "IR", "PUP", "Sus", "NA", "Doubtful"}


def team_code(team):
    return TEAM_ALIASES.get(team, team)


def name_tokens(name, keep_suffix=True):
    tokens = re.sub(r"[^a-z0-9 ]", "", (name or "").lower().replace("-", " ")).split()
    if not keep_suffix:
        tokens = [t for t in tokens if t not in SUFFIXES]
    return " ".join(tokens)


class PlayerIndex:
    """Maps nflverse rows to Sleeper player IDs.

    Order: gsis_id, then full name with suffix plus team, then name without
    suffix plus team, then a name that is unique among active players (a
    player traded since the game). Inactive players and players without a team
    never match by name, so a retired "Kenneth Walker" can't stand in for
    Kenneth Walker III.
    """

    def __init__(self, players):
        self.players = players
        self.by_gsis = {}
        self.by_name_team = {}
        self.by_name = {}
        for pid, p in players.items():
            gsis = (p.get("gsis_id") or "").strip()
            if gsis:
                self.by_gsis[gsis] = pid
            if not (p.get("active") and p.get("team") and p.get("full_name")):
                continue
            for key in {name_tokens(p["full_name"]), name_tokens(p["full_name"], keep_suffix=False)}:
                self.by_name_team.setdefault((key, p["team"]), []).append(pid)
                self.by_name.setdefault(key, []).append(pid)

    def match(self, name, team=None, gsis=None):
        if gsis and gsis in self.by_gsis:
            return self.by_gsis[gsis]
        team = team_code(team) if team else None
        for keep in (True, False):
            key = name_tokens(name, keep)
            hits = self.by_name_team.get((key, team), []) if team else []
            if len(hits) == 1:
                return hits[0]
        for keep in (True, False):
            hits = self.by_name.get(name_tokens(name, keep), [])
            if len(hits) == 1:
                return hits[0]
        return None


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def fantasy_points(row, rec):
    """nflverse fantasy_points is standard scoring; add rec per reception."""
    return fnum(row.get("fantasy_points")) + rec * fnum(row.get("receptions"))


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    with open(path) as f:
        return json.load(f)


def week_games(games, season, week):
    return [g for g in games if g["season"] == str(season) and g["week"] == str(week) and g["game_type"] == "REG"]


def implied(game):
    total, spread = fnum(game["total_line"]), fnum(game["spread_line"])
    home = total / 2 + spread / 2
    return total - home, home


def kickoff(game):
    """'Sun 1:00 PM ET' from nflverse gameday and gametime, which are Eastern."""
    day = datetime.date.fromisoformat(game["gameday"])
    if not game.get("gametime"):
        return f"{day.strftime('%a')} (time unknown)"
    hour, minute = (int(x) for x in game["gametime"].split(":"))
    clock = datetime.time(hour, minute).strftime("%I:%M %p").lstrip("0")
    return f"{day.strftime('%a')} {clock} ET"


def schedule(games, season, week):
    """Team -> (opponent, home, kickoff, game) for the week, plus bye teams."""
    by_team = {}
    teams = set()
    for g in games:
        if g["season"] == str(season):
            teams.update((team_code(g["home_team"]), team_code(g["away_team"])))
    for g in week_games(games, season, week):
        home, away = team_code(g["home_team"]), team_code(g["away_team"])
        by_team[home] = (away, True, kickoff(g), g)
        by_team[away] = (home, False, kickoff(g), g)
    return by_team, sorted(teams - set(by_team))


def get(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "fantasy-skills"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as out:
        out.write(resp.read())
    print(f"saved {path}")


def cmd_fetch(args):
    os.makedirs(args.out, exist_ok=True)
    state_path = os.path.join(args.out, "state.json")
    get(f"{SLEEPER}/state/nfl", state_path)
    state = read_json(state_path)
    season = state["season"]
    week = args.week or state["week"]
    print(f"season {season} week {week}")
    players_path = os.path.join(args.out, "players.json")
    fresh = os.path.exists(players_path) and (
        datetime.datetime.now().timestamp() - os.path.getmtime(players_path) < 12 * 3600
    )
    if not fresh:
        get(f"{SLEEPER}/players/nfl", players_path)
    for lid in args.league:
        get(f"{SLEEPER}/league/{lid}", os.path.join(args.out, f"league-{lid}.json"))
        get(f"{SLEEPER}/league/{lid}/rosters", os.path.join(args.out, f"rosters-{lid}.json"))
        get(f"{SLEEPER}/league/{lid}/users", os.path.join(args.out, f"users-{lid}.json"))
        get(f"{SLEEPER}/league/{lid}/matchups/{week}", os.path.join(args.out, f"matchups-{lid}.json"))
    get(GAMES_CSV, os.path.join(args.out, "games.csv"))
    get(f"{NFLVERSE}/snap_counts/snap_counts_{season}.csv", os.path.join(args.out, f"snap_counts_{season}.csv"))
    get(f"{NFLVERSE}/stats_player/stats_player_week_{season}.csv",
        os.path.join(args.out, f"stats_player_week_{season}.csv"))


def cmd_lines(args):
    games = read_csv(args.games)
    for g in sorted(week_games(games, args.season, args.week), key=lambda g: (g["gameday"], g["gametime"])):
        away_pts, home_pts = implied(g)
        away, home = team_code(g["away_team"]), team_code(g["home_team"])
        print(
            f"{kickoff(g):<16} {away} {away_pts:.1f} @ {home} {home_pts:.1f}"
            f" | spread {g['spread_line']} total {g['total_line']}"
            f" | roof {g['roof'] or '?'} wind {g['wind'] or '-'} temp {g['temp'] or '-'}"
            f" | QBs {g['away_qb_name']} @ {g['home_qb_name']}"
        )
    _, byes = schedule(games, args.season, args.week)
    print("BYE: " + (", ".join(byes) or "none"))


def describe(pid, players, sched):
    p = players.get(pid)
    if not p:
        return f"{pid} (DEF)" if pid.isalpha() else pid
    team = pid if p.get("position") == "DEF" or pid.isalpha() else p.get("team")
    opp = sched.get(team)
    if not team:
        team, game = "no team", "no game"
    elif opp:
        game = f"vs {opp[0]}" if opp[1] else f"@ {opp[0]}"
    else:
        game = "BYE"
    when = opp[2] if opp else ""
    status = p.get("injury_status") or ""
    name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
    return f"{name} ({p.get('position')}, {team}) {game} {when} {status}".rstrip()


def cmd_lineup(args):
    league = read_json(args.league)
    rosters = read_json(args.rosters)
    matchups = read_json(args.matchups)
    players = read_json(args.players)
    sched, byes = schedule(read_csv(args.games), league.get("season", args.season), args.week)
    mine = next(
        (r for r in rosters if r.get("owner_id") == args.owner or args.owner in (r.get("co_owners") or [])), None
    )
    if not mine:
        sys.exit(f"no roster owned by {args.owner}")
    me = next(m for m in matchups if m["roster_id"] == mine["roster_id"])
    opp = next((m for m in matchups if m["matchup_id"] == me["matchup_id"] and m["roster_id"] != me["roster_id"]), None)
    slots = league["roster_positions"]
    print(f"{league.get('name')}: rec {league['scoring_settings'].get('rec')} | slots {' '.join(slots)} | BYE {', '.join(byes)}")
    for label, m in (("ME", me), ("OPPONENT", opp)):
        if not m:
            continue
        roster = next(r for r in rosters if r["roster_id"] == m["roster_id"])
        reserve = set(roster.get("reserve") or [])
        s = roster.get("settings", {})
        print(f"\n{label} roster {m['roster_id']} ({s.get('wins', 0)}-{s.get('losses', 0)})")
        starters = m["starters"]
        for slot, pid in zip(slots, starters):
            print(f"  {slot:<10} {describe(pid, players, sched) if pid != '0' else 'EMPTY'}")
        for pid in m["players"]:
            if pid not in starters:
                print(f"  {'IR' if pid in reserve else 'BN':<10} {describe(pid, players, sched)}")


def snap_keys(name, week, team):
    """Keys that join a stats row to its snap row.

    The two nflverse files spell names differently ("DJ Moore" and "D.J. Moore",
    "Deebo Samuel Sr." and "Deebo Samuel", "Kenny Gainwell" and "Kenneth
    Gainwell"), so the first key drops punctuation and suffixes and the second
    is first initial plus last name.
    """
    tokens = name_tokens(name, keep_suffix=False).split()
    key = (week, team_code(team))
    if not tokens:
        return key + ("",), None
    return key + (" ".join(tokens),), key + (tokens[0][0], tokens[-1])


class SnapIndex:
    def __init__(self, snaps):
        self.full = {}
        self.initial = {}
        for r in snaps:
            full, initial = snap_keys(r["player"], int(r["week"]), r["team"])
            self.full[full] = r
            if initial:
                self.initial.setdefault(initial, []).append(r)

    def pct(self, name, week, team):
        full, initial = snap_keys(name, week, team)
        row = self.full.get(full)
        if row is None and initial and len(self.initial.get(initial, [])) == 1:
            row = self.initial[initial][0]
        return fnum(row["offense_pct"]) if row else None


def usage_rows(stats, snaps, index, since=1, until=None):
    """Regular-season stat rows from week `since` up to but not including `until`."""
    snap = SnapIndex(snaps)
    for r in stats:
        week = int(r["week"])
        if r.get("season_type", "REG") != "REG" or week < since or (until and week >= until):
            continue
        pid = index.match(r["player_display_name"], r["team"], r.get("player_id"))
        yield pid, week, r, snap.pct(r["player_display_name"], week, r["team"])


def cmd_usage(args):
    players = read_json(args.players)
    index = PlayerIndex(players)
    stats, snaps = read_csv(args.stats), read_csv(args.snaps)
    wanted = {}
    for label in args.name:
        name, _, team = label.partition("@")
        pid = index.match(name, team or None)
        if pid:
            wanted[pid] = label
        else:
            print(f"== {label}: no Sleeper player matched, try the full name or name@TEAM")
    rows = {}
    for pid, week, r, pct in usage_rows(stats, snaps, index, args.since):
        if pid in wanted:
            rows.setdefault(pid, []).append((week, r, pct))
    for pid, label in wanted.items():
        p = players[pid]
        print(f"== {p.get('full_name', label)} ({p.get('position', '?')}, {p.get('team', '?')}) {p.get('injury_status') or ''}")
        for week, r, pct in sorted(rows.get(pid, []), key=lambda x: x[0]):
            snap = f"{pct * 100:.0f}%" if pct is not None else "?"
            print(
                f"  wk{week:>2} v {team_code(r['opponent_team']):<3} snap {snap:>4}"
                f" car {int(fnum(r['carries'])):>2} rush {int(fnum(r['rushing_yards'])):>4}"
                f" tgt {int(fnum(r['targets'])):>2} share {fnum(r['target_share']):.2f}"
                f" rec {int(fnum(r['receptions'])):>2} yds {int(fnum(r['receiving_yards'])):>4}"
                f" td {int(fnum(r['rushing_tds']) + fnum(r['receiving_tds']) + fnum(r['passing_tds']))}"
                f" pass {r['completions']}/{r['attempts']} {r['passing_yards']} int {r['passing_interceptions']}"
                f" | pts {fantasy_points(r, args.rec):.1f}"
            )
        if pid not in rows:
            print(f"  no regular-season games since week {args.since}")


def cmd_free_agents(args):
    players = read_json(args.players)
    index = PlayerIndex(players)
    rostered = set()
    for path in args.rosters:
        for r in read_json(path):
            rostered.update(r.get("players") or [])
    sched, byes = schedule(read_csv(args.games), args.season, args.week)
    games = {}
    for pid, week, r, pct in usage_rows(read_csv(args.stats), read_csv(args.snaps), index, until=args.week):
        if pid and pid not in rostered and r["position"] in SKILL_POSITIONS:
            games.setdefault(pid, []).append((week, r, pct))
    for pos in args.position or SKILL_POSITIONS:
        print(f"-- {pos}: available, points per game over each player's last {args.last} games"
              f" (at least {args.min_games}), injured players last")
        rows = []
        for pid, played in games.items():
            p = players[pid]
            if p.get("position") != pos or not p.get("team"):
                continue
            recent = sorted(played, key=lambda x: x[0])[-args.last:]
            if len(recent) < args.min_games:
                continue
            avg = sum(fantasy_points(r, args.rec) for _, r, _ in recent) / len(recent)
            hurt = p.get("injury_status") in UNAVAILABLE
            rows.append((hurt, -avg, pid, recent))
        for hurt, neg_avg, pid, recent in sorted(rows)[: args.top]:
            p = players[pid]
            opp = sched.get(p["team"])
            if opp:
                away_pts, home_pts = implied(opp[3])
                game = f"implied {home_pts if opp[1] else away_pts:.1f}, {opp[2]}"
            else:
                game = "BYE"
            snaps = ",".join(f"{pct * 100:.0f}" if pct is not None else "?" for _, _, pct in recent)
            tgt = sum(int(fnum(r["targets"])) for _, r, _ in recent)
            car = sum(int(fnum(r["carries"])) for _, r, _ in recent)
            weeks = ",".join(str(w) for w, _, _ in recent)
            print(
                f"  {p['full_name']:<24} {p['team']:<4} {-neg_avg:5.1f}/g wk {weeks}"
                f" | snaps {snaps} tgt {tgt} car {car} | {game} | {p.get('injury_status') or 'healthy'}"
            )


def cmd_offense(args):
    stats = read_csv(args.stats)
    lost = [c for c in (stats[0].keys() if stats else []) if c.endswith("fumbles_lost")]
    for team in args.team:
        team = team_code(team)
        games, sacks, giveaways = set(), 0.0, 0.0
        for r in stats:
            if team_code(r["team"]) != team or r.get("season_type", "REG") != "REG":
                continue
            games.add(r["week"])
            sacks += fnum(r["sacks_suffered"])
            giveaways += fnum(r["passing_interceptions"]) + sum(fnum(r[c]) for c in lost)
        n = len(games) or 1
        print(f"{team}: {len(games)} games, sacks allowed {sacks / n:.1f}/g, giveaways {giveaways / n:.1f}/g")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fetch", help="download Sleeper and nflverse data")
    p.add_argument("--out", required=True)
    p.add_argument("--league", action="append", required=True)
    p.add_argument("--week", type=int)
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("lines", help="kickoffs, implied totals, weather and byes for a week")
    p.add_argument("--games", required=True)
    p.add_argument("--season", required=True)
    p.add_argument("--week", type=int, required=True)
    p.set_defaults(func=cmd_lines)

    p = sub.add_parser("lineup", help="the user's lineup and bench next to their opponent's")
    for flag in ("--league", "--rosters", "--matchups", "--players", "--games", "--owner"):
        p.add_argument(flag, required=True)
    p.add_argument("--season")
    p.add_argument("--week", type=int, required=True)
    p.set_defaults(func=cmd_lineup)

    p = sub.add_parser("usage", help="weekly snaps, touches and points for named players")
    for flag in ("--stats", "--snaps", "--players"):
        p.add_argument(flag, required=True)
    p.add_argument("--rec", type=float, required=True, help="points per reception: 1, 0.5 or 0")
    p.add_argument("--name", action="append", required=True, help="full name, or name@TEAM to disambiguate")
    p.add_argument("--since", type=int, default=1, help="first week to show")
    p.set_defaults(func=cmd_usage)

    p = sub.add_parser("free-agents", help="available players ranked by points per game")
    for flag in ("--stats", "--snaps", "--players", "--games", "--season"):
        p.add_argument(flag, required=True)
    p.add_argument("--rosters", action="append", required=True)
    p.add_argument("--week", type=int, required=True, help="the week being set, byes are taken from it")
    p.add_argument("--rec", type=float, required=True)
    p.add_argument("--last", type=int, default=4, help="games per player to average")
    p.add_argument("--min-games", type=int, default=2)
    p.add_argument("--top", type=int, default=8)
    p.add_argument("--position", action="append", choices=SKILL_POSITIONS)
    p.set_defaults(func=cmd_free_agents)

    p = sub.add_parser("offense", help="sacks allowed and giveaways per game, for DEF streams")
    p.add_argument("--stats", required=True)
    p.add_argument("--team", action="append", required=True)
    p.set_defaults(func=cmd_offense)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
