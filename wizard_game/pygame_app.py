import math
from dataclasses import dataclass
from pathlib import Path

from lisp import LispSyntaxError, parse_many

from .cli import status
from .model import SPELLS, WizardGame
from .scripting import GameSession


BOARD_WIDTH = 720
BOARD_HEIGHT = 540
PANEL_WIDTH = 320
TERMINAL_HEIGHT = 230
WINDOW_SIZE = (BOARD_WIDTH + PANEL_WIDTH, BOARD_HEIGHT + TERMINAL_HEIGHT)
CELL_SIZE = 36


COLORS = {
    "background": (11, 13, 25),
    "floor": (31, 35, 51),
    "floor_alt": (35, 39, 57),
    "grid": (53, 58, 78),
    "wall": (76, 72, 94),
    "wall_edge": (119, 109, 139),
    "panel": (19, 21, 35),
    "terminal": (8, 10, 18),
    "text": (224, 224, 230),
    "muted": (145, 148, 164),
    "gandalf": (226, 92, 82),
    "merlin": (84, 139, 232),
    "health": (92, 194, 117),
    "mana": (83, 151, 229),
    "error": (244, 112, 112),
    "accent": (223, 190, 102),
}


SPELL_COLORS = {
    "огненный шар": (255, 116, 45),
    "ледяной осколок": (87, 218, 238),
    "молния": (255, 231, 92),
}


@dataclass
class VisualEffect:
    event: object
    started_at: int
    duration: int = 650


class TerminalState:
    def __init__(self):
        self.input = ""
        self.lines = []
        self.histories = {}
        self.history_index = -1
        self.scroll = 0

    def write(self, text, color=None):
        for line in str(text).splitlines() or [""]:
            self.lines.append((line, color or COLORS["text"]))
        self.lines = self.lines[-500:]
        self.scroll = 0

    def remember(self, wizard_name, source):
        history = self.histories.setdefault(wizard_name, [])
        if not history or history[-1] != source:
            history.append(source)
        self.history_index = -1

    def previous(self, wizard_name):
        history = self.histories.get(wizard_name, [])
        if not history:
            return self.input
        self.history_index = min(self.history_index + 1, len(history) - 1)
        self.input = history[-self.history_index - 1]
        return self.input

    def next(self, wizard_name):
        if self.history_index <= 0:
            self.history_index = -1
            self.input = ""
            return self.input
        self.history_index -= 1
        history = self.histories.get(wizard_name, [])
        self.input = history[-self.history_index - 1]
        return self.input


class StrategySetup:
    def __init__(self, session):
        self.session = session
        self.names = tuple(wizard.name for wizard in session.game.wizards)
        self.buffers = {name: [] for name in self.names}
        self.index = 0
        self.manual = False

    @property
    def active_name(self):
        return None if self.finished else self.names[self.index]

    @property
    def finished(self):
        return self.index >= len(self.names)

    def append(self, source):
        expressions = parse_many(source)
        if not expressions:
            raise LispSyntaxError("Пустой фрагмент стратегии")
        self.buffers[self.active_name].append(source)
        return len(self.buffers[self.active_name])

    def clear(self):
        self.buffers[self.active_name].clear()

    def source(self, name=None):
        return "\n".join(self.buffers[name or self.active_name])

    def finish(self):
        name = self.active_name
        source = self.source(name)
        if not source.strip():
            raise ValueError("Стратегия пуста")
        self.session.load_strategy(name, source)
        self.index += 1
        return name

    def use_manual_mode(self):
        self.manual = True
        self.index = len(self.names)


class WizardGameApp:
    def __init__(self, pygame_module=None):
        if pygame_module is None:
            try:
                import pygame as pygame_module
            except ImportError as error:
                raise RuntimeError("Для графической игры установите зависимости: pip install -e .") from error

        self.pg = pygame_module
        self.pg.init()
        self.screen = self.pg.display.set_mode(WINDOW_SIZE)
        self.pg.display.set_caption("Битва магов — Lisp")
        self.clock = self.pg.time.Clock()
        self.font = self.pg.font.SysFont("segoeui", 17)
        self.small_font = self.pg.font.SysFont("segoeui", 14)
        self.title_font = self.pg.font.SysFont("georgia", 25, bold=True)
        self.mono_font = self.pg.font.SysFont("consolas", 16)
        self.large_font = self.pg.font.SysFont("georgia", 48, bold=True)
        self.session = GameSession()
        self.setup = StrategySetup(self.session)
        self.battle_started = False
        self.terminal = TerminalState()
        self.effects = []
        self.event_index = 0
        self.running = True
        self.show_help = False
        self.auto_running = False
        self.last_auto_turn = 0
        self.visibility_key = None
        self.visibility_surface = None
        self.terminal.write(
            "Введите стратегию Гэндальфа и завершите её словом finish. F1 — справка.",
            COLORS["accent"],
        )
        self._init_clipboard()

    @property
    def game(self):
        return self.session.game

    @property
    def prompt_name(self):
        return self.setup.active_name if not self.battle_started else self.game.active_wizard.name

    def _init_clipboard(self):
        try:
            self.pg.scrap.init()
        except self.pg.error:
            pass

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        self.pg.quit()

    def handle_events(self):
        for event in self.pg.event.get():
            if event.type == self.pg.QUIT:
                self.running = False
            elif event.type == self.pg.MOUSEWHEEL:
                self.terminal.scroll = max(0, self.terminal.scroll + event.y)
            elif event.type == self.pg.KEYDOWN:
                self._handle_key(event)

    def _handle_key(self, event):
        modifiers = self.pg.key.get_mods()
        if event.key == self.pg.K_ESCAPE:
            if self.show_help:
                self.show_help = False
            else:
                self.running = False
        elif event.key == self.pg.K_F1:
            self.show_help = not self.show_help
        elif event.key == self.pg.K_RETURN:
            if modifiers & self.pg.KMOD_SHIFT:
                self.terminal.input += "\n"
            else:
                self.submit()
        elif event.key == self.pg.K_BACKSPACE:
            self.terminal.input = self.terminal.input[:-1]
        elif event.key == self.pg.K_UP:
            self.terminal.previous(self.prompt_name)
        elif event.key == self.pg.K_DOWN:
            self.terminal.next(self.prompt_name)
        elif event.key == self.pg.K_TAB:
            self.terminal.input += "  "
        elif event.key == self.pg.K_PAGEUP:
            self.terminal.scroll += 4
        elif event.key == self.pg.K_PAGEDOWN:
            self.terminal.scroll = max(0, self.terminal.scroll - 4)
        elif event.key == self.pg.K_v and modifiers & self.pg.KMOD_CTRL:
            self.terminal.input += self._clipboard_text()
        elif event.unicode and event.unicode.isprintable():
            self.terminal.input += event.unicode

    def _clipboard_text(self):
        try:
            value = self.pg.scrap.get(self.pg.SCRAP_TEXT)
            if not value:
                return ""
            return value.decode("utf-8", errors="replace").replace("\x00", "")
        except (self.pg.error, UnicodeError):
            return ""

    def submit(self):
        source = self.terminal.input.strip()
        self.terminal.input = ""
        if not source:
            return

        wizard_name = self.prompt_name
        self.terminal.remember(wizard_name, source)
        self.terminal.write(f"{wizard_name}> {source}", self._wizard_color(wizard_name))

        if source == "help":
            self.show_help = True
            return
        if source == "clear":
            self.terminal.lines.clear()
            return
        if source == "history":
            history = self.terminal.histories.get(wizard_name, [])
            self.terminal.write("\n".join(history) if history else "История пуста", COLORS["muted"])
            return
        if source == "state":
            if self.battle_started:
                self.terminal.write(status(self.game), COLORS["muted"])
            else:
                count = len(self.setup.buffers[self.setup.active_name])
                self.terminal.write(f"Фрагментов в текущей стратегии: {count}", COLORS["muted"])
            return
        if source == "restart":
            self._restart()
            return
        if source in {"quit", "exit"}:
            self.running = False
            return
        if not self.battle_started:
            self._submit_setup(source)
            return
        if source == "auto":
            if not self.session.strategies_ready:
                self.terminal.write("Сначала задайте обе стратегии", COLORS["error"])
                return
            self.auto_running = not self.auto_running
            state = "запущен" if self.auto_running else "остановлен"
            self.terminal.write(f"Автобой {state}", COLORS["accent"])
            return
        if source.startswith("load "):
            self._load(source[5:].strip().strip('"'))
            return

        self._execute(source)

    def _execute(self, source):
        result = self.session.execute(source)
        color = COLORS["error"] if result.error else COLORS["text"]
        self.terminal.write(self.session.format_result(result), color)
        self._collect_effects()
        if self.game.game_over:
            self.auto_running = False

    def _submit_setup(self, source):
        if source == "finish":
            try:
                name = self.setup.finish()
            except Exception as error:
                self.terminal.write(f"Ошибка стратегии: {error}", COLORS["error"])
                return
            self.terminal.write(f"Стратегия {name} принята", self._wizard_color(name))
            if self.setup.finished:
                self.battle_started = True
                self.auto_running = True
                self.last_auto_turn = self.pg.time.get_ticks()
                self.terminal.write("Обе стратегии готовы. Дуэль начинается.", COLORS["accent"])
            else:
                self.terminal.write(
                    f"Теперь введите стратегию для {self.setup.active_name} и завершите её словом finish.",
                    self._wizard_color(self.setup.active_name),
                )
            return
        if source == "manual":
            self.setup.use_manual_mode()
            self.battle_started = True
            self.auto_running = False
            self.terminal.write("Ручной режим. Команды выполняются по очереди.", COLORS["accent"])
            return
        if source == "strategy":
            draft = self.setup.source()
            self.terminal.write(draft if draft else "Стратегия пока пуста", COLORS["muted"])
            return
        if source == "reset-strategy":
            self.setup.clear()
            self.terminal.write("Текущая стратегия очищена", COLORS["muted"])
            return
        if source == "auto":
            self.terminal.write("Сначала завершите обе стратегии словом finish", COLORS["error"])
            return
        if source.startswith("load "):
            self._load(source[5:].strip().strip('"'))
            return
        try:
            count = self.setup.append(source)
            self.terminal.write(f"Фрагмент {count} добавлен. Продолжайте или введите finish.", COLORS["muted"])
        except Exception as error:
            self.terminal.write(f"Синтаксическая ошибка: {error}", COLORS["error"])

    def _load(self, filename):
        try:
            source = Path(filename).read_text(encoding="utf-8")
        except OSError as error:
            self.terminal.write(f"Ошибка: {error}", COLORS["error"])
            return
        if not self.battle_started:
            try:
                self.setup.append(source)
            except Exception as error:
                self.terminal.write(f"Ошибка стратегии: {error}", COLORS["error"])
                return
            self.terminal.write(f"Файл {filename} добавлен. Введите finish.", COLORS["accent"])
        else:
            try:
                self.session.load_strategy(self.game.active_wizard.name, source)
            except Exception as error:
                self.terminal.write(f"Ошибка стратегии: {error}", COLORS["error"])
                return
            self.terminal.write(f"Стратегия из {filename} загружена", COLORS["accent"])

    def _restart(self):
        self.session = GameSession(WizardGame())
        self.setup = StrategySetup(self.session)
        self.battle_started = False
        self.effects.clear()
        self.event_index = 0
        self.auto_running = False
        self.visibility_key = None
        self.visibility_surface = None
        self.terminal.write("Новая дуэль началась", COLORS["accent"])

    def _collect_effects(self):
        now = self.pg.time.get_ticks()
        for event in self.game.events[self.event_index:]:
            self.effects.append(VisualEffect(event, now))
        self.event_index = len(self.game.events)

    def update(self):
        now = self.pg.time.get_ticks()
        self.effects = [effect for effect in self.effects if now - effect.started_at < effect.duration]
        if self.battle_started and self.auto_running and not self.game.game_over and now - self.last_auto_turn >= 550:
            self.last_auto_turn = now
            result = self.session.execute("(turn)")
            self.terminal.write(
                f"{result.wizard}> (turn) → {self.session.format_result(result)}",
                COLORS["error"] if result.error else self._wizard_color(result.wizard),
            )
            self._collect_effects()
            if result.error or not result.action_used:
                self.auto_running = False

    def draw(self):
        self.screen.fill(COLORS["background"])
        self._draw_arena()
        self._draw_panel()
        self._draw_terminal()
        if self.game.game_over:
            self._draw_game_over()
        if self.show_help:
            self._draw_help()
        self.pg.display.flip()

    def _draw_arena(self):
        for y in range(self.game.arena.height):
            for x in range(self.game.arena.width):
                rect = self.pg.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                if (x, y) in self.game.arena.walls:
                    self.pg.draw.rect(self.screen, COLORS["wall"], rect)
                    self.pg.draw.line(self.screen, COLORS["wall_edge"], rect.topleft, rect.topright, 2)
                    self.pg.draw.line(self.screen, (47, 45, 61), rect.bottomleft, rect.bottomright, 2)
                else:
                    color = COLORS["floor_alt"] if (x + y) % 2 else COLORS["floor"]
                    self.pg.draw.rect(self.screen, color, rect)
                self.pg.draw.rect(self.screen, COLORS["grid"], rect, 1)

        self._draw_visibility()
        now = self.pg.time.get_ticks()
        for effect in self.effects:
            self._draw_effect(effect, now)
        for wizard in self.game.wizards:
            self._draw_wizard(wizard, now)

    def _draw_visibility(self):
        key = tuple((wizard.x, wizard.y, wizard.vision_range, wizard.alive) for wizard in self.game.wizards)
        if key == self.visibility_key and self.visibility_surface is not None:
            self.screen.blit(self.visibility_surface, (0, 0))
            return
        overlay = self.pg.Surface((BOARD_WIDTH, BOARD_HEIGHT), self.pg.SRCALPHA)
        for wizard in self.game.wizards:
            if not wizard.alive:
                continue
            color = (*self._wizard_color(wizard.name), 14)
            for y in range(self.game.arena.height):
                for x in range(self.game.arena.width):
                    if self.game.arena.visible((wizard.x, wizard.y), (x, y), wizard.vision_range):
                        self.pg.draw.rect(overlay, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        self.visibility_key = key
        self.visibility_surface = overlay
        self.screen.blit(overlay, (0, 0))

    def _draw_wizard(self, wizard, now):
        x = wizard.x * CELL_SIZE + CELL_SIZE // 2
        y = wizard.y * CELL_SIZE + CELL_SIZE // 2
        color = self._wizard_color(wizard.name)
        pulse = 2 + int(2 * (1 + math.sin(now / 220)))
        aura = self.pg.Surface((56, 56), self.pg.SRCALPHA)
        self.pg.draw.circle(aura, (*color, 45), (28, 28), 22 + pulse)
        self.screen.blit(aura, (x - 28, y - 28))
        self.pg.draw.ellipse(self.screen, (8, 9, 16), (x - 13, y + 12, 27, 8))
        self.pg.draw.polygon(self.screen, color, [(x, y - 11), (x - 13, y + 15), (x + 13, y + 15)])
        self.pg.draw.circle(self.screen, (232, 207, 177), (x, y - 10), 8)
        self.pg.draw.line(self.screen, COLORS["accent"], (x + 10, y - 6), (x + 14, y + 16), 3)
        initial = self.small_font.render(wizard.name[0], True, (18, 18, 24))
        self.screen.blit(initial, initial.get_rect(center=(x, y + 5)))
        label = self.small_font.render(wizard.name, True, COLORS["text"])
        self.screen.blit(label, label.get_rect(midbottom=(x, y - 22)))

    def _draw_effect(self, effect, now):
        event = effect.event
        progress = min(1, (now - effect.started_at) / effect.duration)
        alpha = max(0, int(255 * (1 - progress)))
        start = self._cell_center(event.start)
        end = self._cell_center(event.end)
        layer = self.pg.Surface((BOARD_WIDTH, BOARD_HEIGHT), self.pg.SRCALPHA)
        if event.kind == "move":
            radius = int(8 + progress * 25)
            self.pg.draw.circle(layer, (*self._wizard_color(event.actor), alpha), end, radius, 3)
        elif event.kind == "cast":
            color = SPELL_COLORS.get(event.spell, COLORS["accent"])
            width = max(1, int(7 * (1 - progress)))
            self.pg.draw.line(layer, (*color, alpha), start, end, width)
            radius = int(8 + progress * 22)
            self.pg.draw.circle(layer, (*color, alpha), end, radius, 3)
            for index in range(7):
                fraction = (index + progress * 2) / 8
                if fraction > 1:
                    continue
                px = int(start[0] + (end[0] - start[0]) * fraction)
                py = int(start[1] + (end[1] - start[1]) * fraction)
                self.pg.draw.circle(layer, (*color, alpha), (px, py), 3)
        self.screen.blit(layer, (0, 0))

    def _draw_panel(self):
        panel = self.pg.Rect(BOARD_WIDTH, 0, PANEL_WIDTH, BOARD_HEIGHT)
        self.pg.draw.rect(self.screen, COLORS["panel"], panel)
        self.pg.draw.line(self.screen, COLORS["accent"], panel.topleft, panel.bottomleft, 2)
        title = self.title_font.render("БИТВА МАГОВ", True, COLORS["accent"])
        self.screen.blit(title, (BOARD_WIDTH + 22, 18))
        if self.battle_started:
            caption = f"Ход {self.game.turn}: {self.game.active_wizard.name}"
        else:
            caption = f"Стратегия: {self.setup.active_name}"
        turn = self.font.render(caption, True, COLORS["text"])
        self.screen.blit(turn, (BOARD_WIDTH + 22, 58))

        y = 94
        for wizard in self.game.wizards:
            self._draw_wizard_card(wizard, y)
            y += 120

        heading = self.font.render("Заклинания", True, COLORS["accent"])
        self.screen.blit(heading, (BOARD_WIDTH + 22, y + 3))
        y += 31
        for spell in SPELLS.values():
            color = SPELL_COLORS[spell.name]
            self.pg.draw.circle(self.screen, color, (BOARD_WIDTH + 29, y + 8), 5)
            name = self.small_font.render(spell.name, True, COLORS["text"])
            info = self.small_font.render(
                f"урон {spell.damage} · мана {spell.mana_cost} · {spell.range} кл.",
                True,
                COLORS["muted"],
            )
            self.screen.blit(name, (BOARD_WIDTH + 42, y - 2))
            self.screen.blit(info, (BOARD_WIDTH + 42, y + 16))
            y += 47

        hint = self.small_font.render("F1 справка · Esc выход", True, COLORS["muted"])
        self.screen.blit(hint, (BOARD_WIDTH + 22, BOARD_HEIGHT - 28))

    def _draw_wizard_card(self, wizard, y):
        x = BOARD_WIDTH + 18
        width = PANEL_WIDTH - 36
        rect = self.pg.Rect(x, y, width, 106)
        self.pg.draw.rect(self.screen, (27, 30, 47), rect, border_radius=8)
        border = self._wizard_color(wizard.name) if wizard.name == self.prompt_name else (66, 69, 87)
        self.pg.draw.rect(self.screen, border, rect, 2, border_radius=8)
        name = self.font.render(wizard.name, True, self._wizard_color(wizard.name))
        spell = self.small_font.render(wizard.selected_spell, True, COLORS["muted"])
        self.screen.blit(name, (x + 12, y + 8))
        self.screen.blit(spell, (x + width - spell.get_width() - 12, y + 11))
        self._draw_bar(x + 12, y + 42, width - 24, wizard.health, COLORS["health"], f"HP {max(0, wizard.health)}")
        self._draw_bar(x + 12, y + 70, width - 24, wizard.mana, COLORS["mana"], f"MP {wizard.mana}")

    def _draw_bar(self, x, y, width, value, color, label):
        self.pg.draw.rect(self.screen, (12, 14, 24), (x, y, width, 18), border_radius=4)
        fill = max(0, min(width, int(width * value / 100)))
        if fill:
            self.pg.draw.rect(self.screen, color, (x, y, fill, 18), border_radius=4)
        text = self.small_font.render(label, True, COLORS["text"])
        self.screen.blit(text, (x + 5, y - 1))

    def _draw_terminal(self):
        top = BOARD_HEIGHT
        self.pg.draw.rect(self.screen, COLORS["terminal"], (0, top, WINDOW_SIZE[0], TERMINAL_HEIGHT))
        self.pg.draw.line(self.screen, COLORS["accent"], (0, top), (WINDOW_SIZE[0], top), 2)
        terminal_title = "STRATEGY SETUP" if not self.battle_started else "LISP TERMINAL"
        title = self.small_font.render(terminal_title, True, COLORS["accent"])
        self.screen.blit(title, (12, top + 8))

        output_top = top + 31
        output_bottom = WINDOW_SIZE[1] - 42
        wrapped = []
        for text, color in self.terminal.lines:
            for line in self._wrap(text, self.mono_font, WINDOW_SIZE[0] - 28):
                wrapped.append((line, color))
        visible_count = max(1, (output_bottom - output_top) // 19)
        end = max(0, len(wrapped) - self.terminal.scroll)
        start = max(0, end - visible_count)
        for index, (line, color) in enumerate(wrapped[start:end]):
            rendered = self.mono_font.render(line, True, color)
            self.screen.blit(rendered, (14, output_top + index * 19))

        wizard_name = self.prompt_name
        prompt = f"{wizard_name}> "
        prompt_image = self.mono_font.render(prompt, True, self._wizard_color(wizard_name))
        prompt_y = WINDOW_SIZE[1] - 32
        self.screen.blit(prompt_image, (14, prompt_y))
        available = WINDOW_SIZE[0] - prompt_image.get_width() - 30
        input_line = self.terminal.input.replace("\n", " ↵ ")
        while self.mono_font.size(input_line)[0] > available and input_line:
            input_line = input_line[1:]
        input_image = self.mono_font.render(input_line, True, COLORS["text"])
        input_x = 14 + prompt_image.get_width()
        self.screen.blit(input_image, (input_x, prompt_y))
        if (self.pg.time.get_ticks() // 500) % 2 == 0:
            cursor_x = input_x + input_image.get_width() + 1
            self.pg.draw.line(self.screen, COLORS["text"], (cursor_x, prompt_y), (cursor_x, prompt_y + 18), 1)

    def _draw_help(self):
        shade = self.pg.Surface(WINDOW_SIZE, self.pg.SRCALPHA)
        shade.fill((5, 7, 14, 205))
        self.screen.blit(shade, (0, 0))
        rect = self.pg.Rect(110, 60, WINDOW_SIZE[0] - 220, WINDOW_SIZE[1] - 120)
        self.pg.draw.rect(self.screen, (23, 26, 42), rect, border_radius=12)
        self.pg.draw.rect(self.screen, COLORS["accent"], rect, 2, border_radius=12)
        title = self.title_font.render("СПРАВКА", True, COLORS["accent"])
        self.screen.blit(title, title.get_rect(midtop=(rect.centerx, rect.top + 20)))
        lines = [
            "ПОДГОТОВКА: стратегия Гэндальфа → finish → Мерлина → finish",
            "После второго finish дуэль запускается автоматически.",
            "",
            "(move dx dy)                         шаг на соседнюю клетку",
            '(select-spell "название")            выбрать заклинание',
            '(cast "название" x y)                применить заклинание',
            "(health) (mana) (position)           состояние мага",
            "(enemy-health) (enemy-position)      состояние противника",
            "(distance) (visible?)                 дистанция и видимость",
            "",
            "load путь.lisp    загрузить стратегию активному магу",
            "finish            принять стратегию и перейти к следующей",
            "strategy          показать собранный исходник",
            "reset-strategy    очистить текущую стратегию",
            "manual            перейти к ручному управлению",
            "auto              остановить или продолжить готовый бой",
            "state             вывести состояние в терминал",
            "history / clear   история команд / очистка журнала",
            "restart           начать новую дуэль",
            "",
            "Enter — выполнить · Shift+Enter — новая строка · ↑↓ — история",
            "Ctrl+V — вставить · PageUp/PageDown — прокрутка · F1 — закрыть",
        ]
        y = rect.top + 62
        for line in lines:
            image = self.mono_font.render(line, True, COLORS["text"] if line else COLORS["muted"])
            self.screen.blit(image, (rect.left + 34, y))
            y += 25

    def _draw_game_over(self):
        shade = self.pg.Surface((BOARD_WIDTH, BOARD_HEIGHT), self.pg.SRCALPHA)
        shade.fill((4, 5, 12, 175))
        self.screen.blit(shade, (0, 0))
        winner = self.game.winner
        title = self.large_font.render("ДУЭЛЬ ОКОНЧЕНА", True, COLORS["accent"])
        subtitle = self.title_font.render(
            f"Победитель: {winner.name}" if winner else "Ничья",
            True,
            self._wizard_color(winner.name) if winner else COLORS["text"],
        )
        self.screen.blit(title, title.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2 - 28)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2 + 30)))

    def save_screenshot(self, path):
        self.draw()
        self.pg.image.save(self.screen, str(path))

    def _wizard_color(self, name):
        return COLORS["gandalf"] if name == "Гэндальф" else COLORS["merlin"]

    @staticmethod
    def _cell_center(cell):
        return cell[0] * CELL_SIZE + CELL_SIZE // 2, cell[1] * CELL_SIZE + CELL_SIZE // 2

    @staticmethod
    def _wrap(text, font, width):
        if not text:
            return [""]
        lines = []
        current = ""
        for word in text.split(" "):
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
        return lines


def run():
    WizardGameApp().run()


if __name__ == "__main__":
    run()
