import unittest
from pathlib import Path

from wizard_game import Arena, GameSession, Wizard, WizardGame
from wizard_game.model import GameRuleError
from wizard_game.pygame_app import StrategySetup, TerminalState


def small_game(walls=None):
    arena = Arena(width=7, height=5, walls=set(walls or ()))
    return WizardGame(arena, [Wizard("Гэндальф", 1, 1), Wizard("Мерлин", 3, 1)])


class GameModelTests(unittest.TestCase):
    def test_move(self):
        game = small_game()
        game.move("Гэндальф", 0, 1)
        self.assertEqual((game.wizards[0].x, game.wizards[0].y), (1, 2))
        self.assertEqual((game.events[-1].kind, game.events[-1].end), ("move", (1, 2)))

    def test_move_rejects_long_steps_walls_and_occupied_cells(self):
        game = small_game({(1, 2)})
        for dx, dy in ((2, 0), (0, 1)):
            with self.subTest(move=(dx, dy)), self.assertRaises(GameRuleError):
                game.move("Гэндальф", dx, dy)
        game.wizards[1].x = 2
        with self.assertRaises(GameRuleError):
            game.move("Гэндальф", 1, 0)

    def test_cast_hits_target_and_spends_mana(self):
        game = small_game()
        game.cast("Гэндальф", "огненный шар", 3, 1)
        self.assertEqual(game.wizards[1].health, 70)
        self.assertEqual(game.wizards[0].mana, 80)
        self.assertEqual(game.wizards[0].score, 30)
        self.assertEqual(game.events[-1].spell, "огненный шар")
        self.assertEqual(game.events[-1].target, "Мерлин")

    def test_cast_at_empty_cell_still_spends_mana(self):
        game = small_game()
        game.cast("Гэндальф", "ледяной осколок", 2, 2)
        self.assertEqual(game.wizards[0].mana, 85)
        self.assertEqual(game.wizards[1].health, 100)

    def test_cast_respects_walls_range_and_mana(self):
        game = small_game({(2, 1)})
        with self.assertRaises(GameRuleError):
            game.cast("Гэндальф", "огненный шар", 3, 1)
        game = small_game()
        game.wizards[1].x = 6
        with self.assertRaises(GameRuleError):
            game.cast("Гэндальф", "ледяной осколок", 6, 1)
        game.wizards[0].mana = 0
        with self.assertRaises(GameRuleError):
            game.cast("Гэндальф", "молния", 6, 1)

    def test_winner(self):
        game = small_game()
        for _ in range(3):
            game.wizards[0].mana = 100
            game.cast("Гэндальф", "молния", 3, 1)
        self.assertTrue(game.game_over)
        self.assertEqual(game.winner.name, "Гэндальф")
        self.assertEqual(game.wizards[0].score, 100)
        with self.assertRaises(GameRuleError):
            game.move("Гэндальф", 0, 1)

    def test_end_turn_regenerates_and_switches_actor(self):
        game = small_game()
        game.wizards[0].mana = 80
        game.end_turn()
        self.assertEqual(game.wizards[0].mana, 85)
        self.assertEqual(game.active_wizard.name, "Мерлин")

    def test_board_contains_wizards_and_walls(self):
        board = small_game({(2, 2)}).board()
        self.assertIn("G.M", board)
        self.assertIn("#", board)


class ScriptingTests(unittest.TestCase):
    def setUp(self):
        self.session = GameSession(small_game())

    def test_queries_do_not_end_turn(self):
        result = self.session.execute("(list (health) (mana) (position) (distance))")
        self.assertEqual(result.value, [100, 100, [1, 1], 2])
        self.assertFalse(result.action_used)
        self.assertEqual(self.session.game.active_wizard.name, "Гэндальф")

    def test_move_ends_turn(self):
        result = self.session.execute("(move 0 1)")
        self.assertTrue(result.ok)
        self.assertTrue(result.action_used)
        self.assertEqual(self.session.game.active_wizard.name, "Мерлин")

    def test_only_one_action_is_allowed(self):
        result = self.session.execute("(begin (move 0 1) (move 0 1))")
        self.assertFalse(result.ok)
        self.assertTrue(result.action_used)
        self.assertEqual((self.session.game.wizards[0].x, self.session.game.wizards[0].y), (1, 2))
        self.assertEqual(self.session.game.active_wizard.name, "Мерлин")

    def test_cannot_control_the_opponent(self):
        result = self.session.execute('(move-wizard "Мерлин" 0 1)')
        self.assertFalse(result.ok)
        self.assertFalse(result.action_used)

    def test_compatibility_commands_accept_vectors(self):
        result = self.session.execute('(move-wizard "Гэндальф" [0 1])')
        self.assertTrue(result.ok)
        self.assertEqual((self.session.game.wizards[0].x, self.session.game.wizards[0].y), (1, 2))

    def test_select_and_cast_in_one_expression(self):
        result = self.session.execute('(begin (select-spell "молния") (cast 3 1))')
        self.assertTrue(result.ok)
        self.assertEqual(self.session.game.wizards[1].health, 60)

    def test_interpreters_do_not_share_player_definitions(self):
        self.session.execute("(define secret 42)")
        self.session.execute("(move 0 1)")
        result = self.session.execute("secret")
        self.assertFalse(result.ok)

    def test_error_before_action_keeps_turn(self):
        result = self.session.execute("(/ 1 0)")
        self.assertFalse(result.ok)
        self.assertFalse(result.action_used)
        self.assertEqual(self.session.game.active_wizard.name, "Гэндальф")

    def test_invalid_action_keeps_turn(self):
        result = self.session.execute("(move 3 0)")
        self.assertFalse(result.ok)
        self.assertFalse(result.action_used)
        self.assertEqual(self.session.game.active_wizard.name, "Гэндальф")

    def test_getters_for_legacy_strategies(self):
        result = self.session.execute(
            '(list (get-wizard-health "Мерлин") '
            '(get-distance "Гэндальф" "Мерлин") '
            '(is-wizard-visible "Гэндальф" "Мерлин"))'
        )
        self.assertEqual(result.value, [100, 2, True])

    def test_example_strategies_load_and_take_a_turn(self):
        root = Path(__file__).resolve().parents[1]
        gandalf = (root / "examples" / "gandalf.lisp").read_text(encoding="utf-8")
        merlin = (root / "examples" / "merlin.lisp").read_text(encoding="utf-8")
        self.assertTrue(self.session.execute(gandalf).ok)
        self.assertTrue(self.session.execute("(turn)").action_used)
        self.assertTrue(self.session.execute(merlin).ok)
        self.assertTrue(self.session.execute("(turn)").action_used)

    def test_strategy_loader_requires_turn_function(self):
        with self.assertRaises(Exception):
            self.session.load_strategy("Гэндальф", "(define answer 42)")
        self.assertFalse(self.session.controllers["Гэндальф"].strategy_loaded)

    def test_strategy_loader_does_not_allow_top_level_actions(self):
        start = self.session.game.wizards[0].x, self.session.game.wizards[0].y
        source = "(move 0 1) (define (turn) (move 0 1))"
        with self.assertRaises(Exception):
            self.session.load_strategy("Гэндальф", source)
        self.assertEqual((self.session.game.wizards[0].x, self.session.game.wizards[0].y), start)
        with self.assertRaises(Exception):
            self.session.load_strategy(
                "Гэндальф",
                '(select-spell "молния") (define (turn) (move 0 1))',
            )
        self.assertEqual(self.session.game.wizards[0].selected_spell, "огненный шар")

    def test_both_strategies_can_be_preloaded_before_battle(self):
        root = Path(__file__).resolve().parents[1]
        for name, filename in (("Гэндальф", "gandalf.lisp"), ("Мерлин", "merlin.lisp")):
            source = (root / "examples" / filename).read_text(encoding="utf-8")
            self.session.load_strategy(name, source)
        self.assertTrue(self.session.strategies_ready)
        self.assertTrue(self.session.execute("(turn)").action_used)

    def test_example_strategies_can_finish_default_duel(self):
        root = Path(__file__).resolve().parents[1]
        session = GameSession()
        sources = {
            "Гэндальф": (root / "examples" / "gandalf.lisp").read_text(encoding="utf-8"),
            "Мерлин": (root / "examples" / "merlin.lisp").read_text(encoding="utf-8"),
        }
        loaded = set()
        for _ in range(100):
            name = session.game.active_wizard.name
            if name not in loaded:
                self.assertTrue(session.execute(sources[name]).ok)
                loaded.add(name)
            result = session.execute("(turn)")
            self.assertTrue(result.action_used, result.error)
            if session.game.game_over:
                break
        self.assertTrue(session.game.game_over)


class TerminalStateTests(unittest.TestCase):
    def test_history_is_separate_for_each_wizard(self):
        terminal = TerminalState()
        terminal.remember("Гэндальф", "(+ 1 2)")
        terminal.remember("Мерлин", "(health)")
        self.assertEqual(terminal.previous("Гэндальф"), "(+ 1 2)")
        terminal.history_index = -1
        self.assertEqual(terminal.previous("Мерлин"), "(health)")

    def test_output_is_split_into_lines(self):
        terminal = TerminalState()
        terminal.write("first\nsecond")
        self.assertEqual([line for line, _color in terminal.lines], ["first", "second"])


class StrategySetupTests(unittest.TestCase):
    def setUp(self):
        self.session = GameSession(small_game())
        self.setup = StrategySetup(self.session)

    def test_finish_switches_from_gandalf_to_merlin(self):
        self.setup.append("(define (turn) (move 0 1))")
        self.assertEqual(self.setup.finish(), "Гэндальф")
        self.assertEqual(self.setup.active_name, "Мерлин")
        self.assertFalse(self.setup.finished)

    def test_invalid_strategy_does_not_advance(self):
        self.setup.append("(define answer 42)")
        with self.assertRaises(Exception):
            self.setup.finish()
        self.assertEqual(self.setup.active_name, "Гэндальф")

    def test_second_finish_makes_both_strategies_ready(self):
        self.setup.append("(define (turn) (move 0 1))")
        self.setup.finish()
        self.setup.append("(define (turn) (move 0 1))")
        self.setup.finish()
        self.assertTrue(self.setup.finished)
        self.assertTrue(self.session.strategies_ready)

    def test_manual_mode_skips_setup(self):
        self.setup.use_manual_mode()
        self.assertTrue(self.setup.finished)
        self.assertTrue(self.setup.manual)


if __name__ == "__main__":
    unittest.main()
