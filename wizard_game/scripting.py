from dataclasses import dataclass

from lisp import Interpreter, LispNameError, Symbol, Vector

from .model import GameRuleError, SPELLS, WizardGame


@dataclass(frozen=True)
class TurnResult:
    wizard: str
    value: object = None
    error: str | None = None
    action_used: bool = False

    @property
    def ok(self):
        return self.error is None


class WizardController:
    def __init__(self, game, wizard_name):
        self.game = game
        self.wizard_name = wizard_name
        self.interpreter = Interpreter()
        self.action_used = False
        self.loading_strategy = False
        self.strategy_loaded = False
        self._install_commands()

    def begin_turn(self):
        self.action_used = False

    def _check_action(self):
        if self.loading_strategy:
            raise GameRuleError("Игровые действия нельзя выполнять при загрузке стратегии")
        if self.action_used:
            raise GameRuleError("За один ход доступно только одно действие")
        if self.game.active_wizard.name != self.wizard_name:
            raise GameRuleError("Сейчас ход другого мага")

    def _install_commands(self):
        commands = {
            "move": self.move,
            "move-wizard": self.move_wizard,
            "select-spell": self.select_spell,
            "cast": self.cast,
            "cast-spell": self.cast_spell,
            "health": lambda: self.wizard.health,
            "mana": lambda: self.wizard.mana,
            "position": lambda: Vector((self.wizard.x, self.wizard.y)),
            "enemy-position": lambda: Vector((self.enemy.x, self.enemy.y)),
            "enemy-health": lambda: self.enemy.health,
            "distance": lambda: self.game.distance(self.wizard_name, self.enemy.name),
            "visible?": lambda: self.game.is_visible(self.wizard_name, self.enemy.name),
            "get-wizard-health": self.get_wizard_health,
            "get-distance": self.get_distance,
            "is-wizard-visible": self.is_wizard_visible,
            "spell-damage": lambda name: self._spell(name).damage,
            "spell-cost": lambda name: self._spell(name).mana_cost,
            "spell-range": lambda name: self._spell(name).range,
        }
        for name, function in commands.items():
            self.interpreter.define(name, function)

    @property
    def wizard(self):
        return self.game.wizard(self.wizard_name)

    @property
    def enemy(self):
        return self.game.opponent_of(self.wizard)

    def move(self, dx, dy):
        self._check_action()
        result = self.game.move(self.wizard_name, dx, dy)
        self.action_used = True
        return result

    def load_strategy(self, source):
        previous = self.interpreter
        self.interpreter = Interpreter()
        self._install_commands()
        self.loading_strategy = True
        try:
            result = self.interpreter.execute(source)
            try:
                turn = self.interpreter.global_environment.get(Symbol("turn"))
            except LispNameError as error:
                raise GameRuleError("Стратегия должна определить функцию (turn)") from error
            if not callable(turn):
                raise GameRuleError("Стратегия должна определить функцию (turn)")
        except Exception:
            self.interpreter = previous
            raise
        finally:
            self.loading_strategy = False
        self.strategy_loaded = True
        return result

    def move_wizard(self, *arguments):
        if len(arguments) == 2 and isinstance(arguments[1], (list, Vector)):
            name, movement = arguments
            dx, dy = self._coordinates(movement)
        elif len(arguments) == 3:
            name, dx, dy = arguments
        else:
            raise GameRuleError("move-wizard: ожидаются имя и две координаты")
        self._own_name(name)
        return self.move(dx, dy)

    def select_spell(self, *arguments):
        if self.loading_strategy:
            raise GameRuleError("Игровые действия нельзя выполнять при загрузке стратегии")
        if len(arguments) == 1:
            name, spell = self.wizard_name, arguments[0]
        elif len(arguments) == 2:
            name, spell = arguments
        else:
            raise GameRuleError("select-spell: ожидается название заклинания")
        self._own_name(name)
        return self.game.select_spell(self.wizard_name, spell)

    def cast(self, *arguments):
        if len(arguments) == 2 and isinstance(arguments[1], (list, Vector)):
            spell, target = arguments
            target_x, target_y = self._coordinates(target)
        elif len(arguments) == 3:
            spell, target_x, target_y = arguments
        elif len(arguments) == 2:
            target_x, target_y = arguments
            spell = self.wizard.selected_spell
        else:
            raise GameRuleError("cast: ожидаются заклинание и координаты цели")
        self._check_action()
        result = self.game.cast(self.wizard_name, spell, target_x, target_y)
        self.action_used = True
        return result

    def cast_spell(self, *arguments):
        if len(arguments) == 3 and isinstance(arguments[2], (list, Vector)):
            name, spell, target = arguments
            target_x, target_y = self._coordinates(target)
        elif len(arguments) == 4:
            name, spell, target_x, target_y = arguments
        else:
            raise GameRuleError("cast-spell: ожидаются имя, заклинание и координаты")
        self._own_name(name)
        return self.cast(spell, target_x, target_y)

    def get_wizard_health(self, name):
        return self.game.wizard(name).health

    def get_distance(self, first, second):
        return self.game.distance(first, second)

    def is_wizard_visible(self, first, second):
        return self.game.is_visible(first, second)

    def _own_name(self, name):
        if name != self.wizard_name:
            raise GameRuleError("Нельзя отдавать команды чужому магу")

    @staticmethod
    def _coordinates(value):
        if not isinstance(value, (list, Vector)) or len(value) != 2:
            raise GameRuleError("Ожидается пара координат")
        return value

    @staticmethod
    def _spell(name):
        try:
            return SPELLS[name]
        except KeyError as error:
            raise GameRuleError(f"Неизвестное заклинание: {name}") from error


class GameSession:
    def __init__(self, game=None):
        self.game = game or WizardGame()
        self.controllers = {
            wizard.name: WizardController(self.game, wizard.name)
            for wizard in self.game.wizards
        }

    def execute(self, source, wizard_name=None):
        name = wizard_name or self.game.active_wizard.name
        if self.game.game_over:
            return TurnResult(name, error="Дуэль уже завершена")
        if name != self.game.active_wizard.name:
            return TurnResult(name, error="Сейчас ход другого мага")

        controller = self.controllers[name]
        controller.begin_turn()
        try:
            value = controller.interpreter.execute(source)
            result = TurnResult(name, value=value, action_used=controller.action_used)
        except Exception as error:
            result = TurnResult(name, error=str(error), action_used=controller.action_used)

        if controller.action_used:
            self.game.end_turn()
        return result

    def load_strategy(self, wizard_name, source):
        try:
            controller = self.controllers[wizard_name]
        except KeyError as error:
            raise GameRuleError(f"Нет мага с именем {wizard_name}") from error
        return controller.load_strategy(source)

    @property
    def strategies_ready(self):
        return all(controller.strategy_loaded for controller in self.controllers.values())

    def format_result(self, result):
        if result.error:
            return f"Ошибка: {result.error}"
        return self.controllers[result.wizard].interpreter.format(result.value)
