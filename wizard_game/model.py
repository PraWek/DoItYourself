from dataclasses import dataclass, field


@dataclass(frozen=True)
class Spell:
    name: str
    damage: int
    mana_cost: int
    range: int


@dataclass(frozen=True)
class GameEvent:
    kind: str
    actor: str
    start: tuple[int, int]
    end: tuple[int, int]
    message: str
    spell: str | None = None
    target: str | None = None


SPELLS = {
    "огненный шар": Spell("огненный шар", damage=30, mana_cost=20, range=5),
    "ледяной осколок": Spell("ледяной осколок", damage=20, mana_cost=15, range=4),
    "молния": Spell("молния", damage=40, mana_cost=35, range=6),
}


@dataclass
class Wizard:
    name: str
    x: int
    y: int
    health: int = 100
    mana: int = 100
    selected_spell: str = "огненный шар"
    direction: tuple[int, int] = (0, 1)
    score: int = 0
    vision_range: int = 6

    @property
    def alive(self):
        return self.health > 0


@dataclass
class Arena:
    width: int = 20
    height: int = 15
    walls: set[tuple[int, int]] = field(default_factory=set)

    @classmethod
    def default(cls):
        arena = cls()
        for x in range(arena.width):
            arena.walls.add((x, 0))
            arena.walls.add((x, arena.height - 1))
        for y in range(arena.height):
            arena.walls.add((0, y))
            arena.walls.add((arena.width - 1, y))
        arena.walls.update({
            (5, 5), (5, 6), (15, 8), (15, 9), (10, 7),
            (10, 8), (7, 10), (8, 10), (12, 3), (13, 3),
        })
        return arena

    def contains(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_open(self, x, y):
        return self.contains(x, y) and (x, y) not in self.walls

    def line(self, start, end):
        """Cells crossed by a shot, excluding its origin."""
        x0, y0 = start
        x1, y1 = end
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        step_x = 1 if x0 < x1 else -1
        step_y = 1 if y0 < y1 else -1
        error = dx + dy
        cells = []

        while (x0, y0) != (x1, y1):
            twice_error = 2 * error
            if twice_error >= dy:
                error += dy
                x0 += step_x
            if twice_error <= dx:
                error += dx
                y0 += step_y
            cells.append((x0, y0))
        return cells

    def visible(self, start, end, max_range):
        if max(abs(end[0] - start[0]), abs(end[1] - start[1])) > max_range:
            return False
        return all(cell not in self.walls for cell in self.line(start, end))


class GameRuleError(ValueError):
    pass


class WizardGame:
    def __init__(self, arena=None, wizards=None):
        self.arena = arena or Arena.default()
        self.wizards = wizards or [
            Wizard("Гэндальф", 16, 11),
            Wizard("Мерлин", 3, 3),
        ]
        self.active_index = 0
        self.turn = 1
        self.log = []
        self.events: list[GameEvent] = []
        self._validate_positions()

    @property
    def active_wizard(self):
        return self.wizards[self.active_index]

    @property
    def winner(self):
        living = [wizard for wizard in self.wizards if wizard.alive]
        return living[0] if len(living) == 1 else None

    @property
    def game_over(self):
        return sum(wizard.alive for wizard in self.wizards) < 2

    def wizard(self, name):
        for wizard in self.wizards:
            if wizard.name == name:
                return wizard
        raise GameRuleError(f"Нет мага с именем {name}")

    def opponent_of(self, wizard):
        return next(other for other in self.wizards if other is not wizard and other.alive)

    def move(self, wizard_name, dx, dy):
        self._ensure_running()
        wizard = self.wizard(wizard_name)
        if not wizard.alive:
            raise GameRuleError("Побеждённый маг не может двигаться")
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (dx, dy)):
            raise GameRuleError("Смещение должно быть целым")
        if max(abs(dx), abs(dy)) != 1:
            raise GameRuleError("За ход можно перейти только на соседнюю клетку")

        target = wizard.x + dx, wizard.y + dy
        if not self.arena.is_open(*target):
            raise GameRuleError("Путь преграждает стена")
        if any((other.x, other.y) == target and other.alive for other in self.wizards):
            raise GameRuleError("Клетка занята другим магом")

        wizard.x, wizard.y = target
        wizard.direction = dx, dy
        message = f"{wizard.name} перемещается в {target}"
        self.log.append(message)
        self.events.append(GameEvent("move", wizard.name, (target[0] - dx, target[1] - dy), target, message))
        return message

    def select_spell(self, wizard_name, spell_name):
        self._ensure_running()
        wizard = self.wizard(wizard_name)
        if not wizard.alive:
            raise GameRuleError("Побеждённый маг не может выбирать заклинание")
        if spell_name not in SPELLS:
            raise GameRuleError(f"Неизвестное заклинание: {spell_name}")
        wizard.selected_spell = spell_name
        return spell_name

    def cast(self, wizard_name, spell_name, target_x, target_y):
        self._ensure_running()
        wizard = self.wizard(wizard_name)
        if not wizard.alive:
            raise GameRuleError("Побеждённый маг не может колдовать")
        if spell_name not in SPELLS:
            raise GameRuleError(f"Неизвестное заклинание: {spell_name}")
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (target_x, target_y)):
            raise GameRuleError("Координаты цели должны быть целыми")
        if not self.arena.contains(target_x, target_y):
            raise GameRuleError("Цель находится за пределами арены")

        spell = SPELLS[spell_name]
        if wizard.mana < spell.mana_cost:
            raise GameRuleError("Недостаточно маны")
        if not self.arena.visible((wizard.x, wizard.y), (target_x, target_y), spell.range):
            raise GameRuleError("Цель вне дальности или закрыта стеной")

        wizard.mana -= spell.mana_cost
        wizard.selected_spell = spell_name
        wizard.direction = self._direction(wizard.x, wizard.y, target_x, target_y)
        target = next(
            (other for other in self.wizards if other is not wizard and (other.x, other.y) == (target_x, target_y)),
            None,
        )
        if target is None:
            message = f"{wizard.name} посылает заклинание в пустую клетку"
        else:
            damage = min(spell.damage, target.health)
            target.health -= spell.damage
            wizard.score += damage
            message = f"{wizard.name} наносит {damage} урона магу {target.name}"
        self.log.append(message)
        self.events.append(
            GameEvent(
                "cast",
                wizard.name,
                (wizard.x, wizard.y),
                (target_x, target_y),
                message,
                spell.name,
                target.name if target is not None else None,
            )
        )
        return message

    def end_turn(self):
        if self.game_over:
            return
        self.active_wizard.mana = min(100, self.active_wizard.mana + 5)
        start = self.active_index
        while True:
            self.active_index = (self.active_index + 1) % len(self.wizards)
            if self.active_wizard.alive or self.active_index == start:
                break
        self.turn += 1

    def distance(self, first_name, second_name):
        first = self.wizard(first_name)
        second = self.wizard(second_name)
        return max(abs(first.x - second.x), abs(first.y - second.y))

    def is_visible(self, first_name, second_name):
        first = self.wizard(first_name)
        second = self.wizard(second_name)
        return self.arena.visible((first.x, first.y), (second.x, second.y), first.vision_range)

    def board(self):
        cells = [["." for _ in range(self.arena.width)] for _ in range(self.arena.height)]
        for x, y in self.arena.walls:
            cells[y][x] = "#"
        marks = ["G", "M"]
        for index, wizard in enumerate(self.wizards):
            if wizard.alive:
                cells[wizard.y][wizard.x] = marks[index] if index < len(marks) else "W"
        return "\n".join("".join(row) for row in cells)

    def _validate_positions(self):
        positions = set()
        for wizard in self.wizards:
            position = wizard.x, wizard.y
            if not self.arena.is_open(*position):
                raise GameRuleError(f"Некорректная позиция мага {wizard.name}")
            if position in positions:
                raise GameRuleError("Маги не могут стоять на одной клетке")
            positions.add(position)

    def _ensure_running(self):
        if self.game_over:
            raise GameRuleError("Дуэль уже завершена")

    @staticmethod
    def _direction(x0, y0, x1, y1):
        return (
            (x1 > x0) - (x1 < x0),
            (y1 > y0) - (y1 < y0),
        )
