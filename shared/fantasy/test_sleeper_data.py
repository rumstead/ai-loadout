import io
import os
import unittest
from contextlib import redirect_stdout

import sleeper_data as sd

SNAPSHOT = os.path.join(os.path.dirname(__file__), "..", "..", "evals", "workspace", "fantasy", "2026-wk10")


class PlayerIndexTest(unittest.TestCase):
    players = {
        "4634": {"full_name": "Kenneth Walker", "position": "WR", "team": None, "active": False},
        "8151": {"full_name": "Kenneth Walker III", "position": "RB", "team": "KC", "active": True},
        "100": {"full_name": "Marvin Harrison", "position": "WR", "team": "ARI", "active": True},
        "200": {"full_name": "Mike Williams", "position": "WR", "team": "PIT", "active": True},
        "201": {"full_name": "Mike Williams", "position": "WR", "team": "NYJ", "active": True},
        "300": {"full_name": "Kyren Williams", "position": "RB", "team": "LAR", "active": True},
        "400": {"full_name": "Amon-Ra St. Brown", "position": "WR", "team": "DET", "active": True,
                "gsis_id": "00-0036963"},
    }

    def setUp(self):
        self.index = sd.PlayerIndex(self.players)

    def test_suffix_never_falls_back_to_inactive_namesake(self):
        self.assertEqual(self.index.match("Kenneth Walker III", "KC"), "8151")
        self.assertEqual(self.index.match("Kenneth Walker III", "SEA"), "8151")

    def test_suffix_dropped_on_one_side(self):
        self.assertEqual(self.index.match("Marvin Harrison Jr.", "ARI"), "100")

    def test_team_breaks_name_ties(self):
        self.assertEqual(self.index.match("Mike Williams", "NYJ"), "201")
        self.assertIsNone(self.index.match("Mike Williams", "BUF"))

    def test_nflverse_rams_code(self):
        self.assertEqual(self.index.match("Kyren Williams", "LA"), "300")

    def test_gsis_wins(self):
        self.assertEqual(self.index.match("Amon Ra St Brown", "XXX", "00-0036963"), "400")

    def test_punctuation(self):
        self.assertEqual(self.index.match("Amon-Ra St. Brown", "DET"), "400")

    def test_name_without_suffix_and_team(self):
        self.assertEqual(self.index.match("Kenneth Walker"), "8151")
        self.assertIsNone(self.index.match("Mike Williams"))


class SnapIndexTest(unittest.TestCase):
    snaps = [
        {"player": "D.J. Moore", "week": "9", "team": "BUF", "offense_pct": "0.81"},
        {"player": "Deebo Samuel", "week": "4", "team": "SF", "offense_pct": "0.7"},
        {"player": "Kenneth Gainwell", "week": "8", "team": "TB", "offense_pct": "0.55"},
        {"player": "Kyren Williams", "week": "9", "team": "LA", "offense_pct": "0.64"},
        {"player": "Mike Williams", "week": "9", "team": "NYJ", "offense_pct": "0.6"},
        {"player": "Malik Williams", "week": "9", "team": "NYJ", "offense_pct": "0.2"},
    ]

    def setUp(self):
        self.index = sd.SnapIndex(self.snaps)

    def test_spellings_differ_between_files(self):
        self.assertEqual(self.index.pct("DJ Moore", 9, "BUF"), 0.81)
        self.assertEqual(self.index.pct("Deebo Samuel Sr.", 4, "SF"), 0.7)
        self.assertEqual(self.index.pct("Kenny Gainwell", 8, "TB"), 0.55)
        self.assertEqual(self.index.pct("Kyren Williams", 9, "LA"), 0.64)

    def test_initial_fallback_needs_a_unique_match(self):
        self.assertEqual(self.index.pct("Mike Williams", 9, "NYJ"), 0.6)
        self.assertIsNone(self.index.pct("Mo Williams", 9, "NYJ"))
        self.assertIsNone(self.index.pct("DJ Moore", 8, "BUF"))


class ScheduleTest(unittest.TestCase):
    games = [
        {"season": "2026", "week": "10", "game_type": "REG", "gameday": "2026-11-15", "gametime": "09:30",
         "away_team": "NE", "home_team": "DET", "spread_line": "2.5", "total_line": "51.5"},
        {"season": "2026", "week": "10", "game_type": "REG", "gameday": "2026-11-15", "gametime": "13:00",
         "away_team": "LA", "home_team": "ARI", "spread_line": "-9.5", "total_line": "40.5"},
        {"season": "2026", "week": "9", "game_type": "REG", "gameday": "2026-11-08", "gametime": "13:00",
         "away_team": "CHI", "home_team": "TB", "spread_line": "1", "total_line": "44"},
    ]

    def test_kickoff_and_byes(self):
        sched, byes = sd.schedule(self.games, 2026, 10)
        self.assertEqual(sched["NE"][2], "Sun 9:30 AM ET")
        self.assertEqual(sched["LAR"][0], "ARI")
        self.assertEqual(byes, ["CHI", "TB"])

    def test_implied_totals(self):
        self.assertEqual(sd.implied(self.games[0]), (24.5, 27.0))
        self.assertEqual(sd.implied(self.games[1]), (25.0, 15.5))

    def test_player_without_a_team(self):
        sched, _ = sd.schedule(self.games, 2026, 10)
        players = {"1": {"full_name": "Kendre Miller", "position": "RB", "team": None}}
        self.assertIn("no team", sd.describe("1", players, sched))
        self.assertNotIn("BYE", sd.describe("1", players, sched))


class PointsTest(unittest.TestCase):
    def test_reception_bonus(self):
        row = {"fantasy_points": "10", "receptions": "4"}
        self.assertEqual(sd.fantasy_points(row, 0.5), 12.0)
        self.assertEqual(sd.fantasy_points(row, 1), 14.0)


@unittest.skipUnless(os.path.isdir(SNAPSHOT), "eval snapshot not present")
class SnapshotTest(unittest.TestCase):
    def run_cmd(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            sd.main(list(argv))
        return out.getvalue()

    def path(self, name):
        return os.path.join(SNAPSHOT, name)

    def test_lineup_shows_bye_and_opponent(self):
        out = self.run_cmd(
            "lineup", "--league", self.path("league-office.json"), "--rosters", self.path("rosters-office.json"),
            "--matchups", self.path("matchups-office.json"), "--players", self.path("players.json"),
            "--games", self.path("games.csv"), "--week", "10", "--owner", "me",
        )
        self.assertRegex(out, r"TE\s+Colston Loveland \(TE, CHI\) BYE")
        self.assertIn("OPPONENT", out)

    def free_agents(self, week, *extra):
        return self.run_cmd(
            "free-agents", "--stats", self.path("stats_player_week_2026.csv"),
            "--snaps", self.path("snap_counts_2026.csv"), "--players", self.path("players.json"),
            "--rosters", self.path("rosters-office.json"), "--games", self.path("games.csv"),
            "--season", "2026", "--week", str(week), "--rec", "0.5", "--top", "500", *extra,
        )

    def test_free_agents_skip_rostered_players(self):
        self.assertNotIn("Kenneth Walker", self.free_agents(10, "--position", "RB"))

    def test_free_agents_rank_healthy_players_first(self):
        rows = [line for line in self.free_agents(10, "--position", "RB").splitlines() if line.startswith("  ")]
        hurt = [any(f"| {s}" in r for s in sd.UNAVAILABLE) for r in rows]
        self.assertIn(True, hurt)
        self.assertEqual(hurt, sorted(hurt))

    def test_free_agents_use_games_before_the_week(self):
        for line in self.free_agents(6, "--position", "TE").splitlines():
            if line.startswith("  "):
                weeks = [int(w) for w in line.split(" wk ")[1].split(" ")[0].split(",")]
                self.assertTrue(2 <= len(weeks) <= 4 and max(weeks) < 6, line)

    def test_usage_joins_snaps_across_spellings(self):
        out = self.run_cmd(
            "usage", "--stats", self.path("stats_player_week_2026.csv"),
            "--snaps", self.path("snap_counts_2026.csv"), "--players", self.path("players.json"),
            "--rec", "0.5", "--name", "DJ Moore", "--name", "Deebo Samuel", "--name", "Nobody Atall",
        )
        self.assertNotIn("snap    ?", out)
        self.assertIn("Deebo Samuel Sr.", out)
        self.assertIn("Nobody Atall: no Sleeper player matched", out)

    def test_offense(self):
        out = self.run_cmd("offense", "--stats", self.path("stats_player_week_2026.csv"), "--team", "LA")
        self.assertRegex(out, r"^LAR: \d+ games, sacks allowed \d+\.\d/g, giveaways \d+\.\d/g$")


if __name__ == "__main__":
    unittest.main()
