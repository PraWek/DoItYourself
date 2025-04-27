import pygame
from typing import List, Tuple, Dict
from all_namespace import namespace, create_move_wizard, cast_spell, create_select_spell, \
    create_get_wizard_health, create_is_wizard_visible, create_get_distance, create_toggle_ai
from tokenize_and_parse import tokenize, parse
from evaluate import evaluate
import random


class Wizard:
    def __init__(self, x: int, y: int, name: str):
        self.x = x
        self.y = y
        self.name = name
        self.health = 100
        self.mana = 100
        self.direction = (0, 1)  # (dx, dy)
        self.selected_spell = "огненный шар"
        self.score = 0
        self.vision_range = 4
        self.original_vision_range = 4

    def get_visible_cells(self, game_map) -> list:
        visible_cells = []
        for dy in range(-self.vision_range, self.vision_range + 1):
            for dx in range(-self.vision_range, self.vision_range + 1):
                check_x = self.x + dx
                check_y = self.y + dy
                if game_map.is_valid_position(check_x, check_y):
                    if (dx * dx + dy * dy) <= self.vision_range * self.vision_range:
                        visible_cells.append((check_x, check_y))
        return visible_cells


class Spell:
    def __init__(self, name: str, damage: int, mana_cost: int, range: int):
        self.name = name
        self.damage = damage
        self.mana_cost = mana_cost
        self.range = range
        self.special_effect = None


class VisualEffect:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], duration: int, size: int):
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.size = size
        self.current_frame = 0


class SpellProjectile:
    def __init__(self, x: int, y: int, dx: int, dy: int, spell: Spell, caster: Wizard):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.spell = spell
        self.caster = caster
        self.distance_traveled = 0
        self.trail_effects = []


class GameMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.walls = set()

    def add_wall(self, x: int, y: int):
        self.walls.add((x, y))

    def is_wall(self, x: int, y: int) -> bool:
        return (x, y) in self.walls

    def is_valid_position(self, x: int, y: int) -> bool:
        return (0 <= x < self.width and
                0 <= y < self.height and
                not self.is_wall(x, y))


class WizardGame:
    def __init__(self):
        self.current_wizard_index = 0
        self.game_map = GameMap(20, 15)
        self.lisp_command_input = ""
        self.game_started = False
        self.countdown = 3
        self.countdown_timer = 0
        self.wizards: List[Wizard] = []
        self.ai_enabled = False
        self.casting_mode = False
        self.visual_effects: List[VisualEffect] = []
        self.spells: Dict[str, Spell] = {
            "огненный шар": Spell("огненный шар", 30, 20, 5),
            "ледяной осколок": Spell("ледяной осколок", 20, 15, 4),
            "молния": Spell("молния", 40, 35, 6)
        }
        self.projectiles: List[SpellProjectile] = []
        self.names = namespace()

        # Separate console states for each wizard
        self.gandalf_console = {
            "input": "",
            "output": "",
            "history": [],
            "history_index": -1
        }
        self.merlin_console = {
            "input": "",
            "output": "",
            "history": [],
            "history_index": -1
        }
        self.active_console = self.gandalf_console
        self.show_help = False
        self.game_over = False

        # Strategy execution tracking
        self.strategy_counters = {
            "Гэндальф": 0,
            "Мерлин": 0
        }

        # Add wizards
        self.gandalf = Wizard(16, 11, "Гэндальф")
        self.merlin = Wizard(3, 3, "Мерлин")
        self.wizards = [self.gandalf, self.merlin]
        self.current_wizard = self.gandalf

        pygame.init()
        self.cell_size = 40
        self.screen_width = self.game_map.width * self.cell_size
        self.screen_height = self.game_map.height * self.cell_size  # Remove extra space for console
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Битва Волшебников")

        self.font = pygame.font.SysFont('Arial', 16)
        self.console_font = pygame.font.SysFont('Courier New', 14)

        self.WALL_COLOR = (100, 100, 100)
        self.FLOOR_COLOR = (200, 200, 200)
        self.WIZARD_COLORS = {
            "Гэндальф": (255, 0, 0),
            "Мерлин": (0, 0, 255)
        }
        self.PROJECTILE_COLORS = {
            "огненный шар": (255, 100, 0),
            "ледяной осколок": (0, 255, 255),
            "молния": (255, 255, 0)
        }

        self.names[0]["move-wizard"] = {"function": create_move_wizard(self)}
        self.names[0]["cast-spell"] = {"function": cast_spell(self)}
        self.names[0]["select-spell"] = {"function": create_select_spell(self)}
        self.names[0]["toggle-ai"] = {"function": create_toggle_ai(self)}
        self.names[0]["get-wizard-health"] = {"function": create_get_wizard_health(self)}
        self.names[0]["is-wizard-visible"] = {"function": create_is_wizard_visible(self)}
        self.names[0]["get-distance"] = {"function": create_get_distance(self)}

        self._setup_game()
        self.clock = pygame.time.Clock()
        self.running = True

    def _setup_game(self):
        # Стены по периметру
        for x in range(self.game_map.width):
            self.game_map.add_wall(x, 0)
            self.game_map.add_wall(x, self.game_map.height - 1)
        for y in range(self.game_map.height):
            self.game_map.add_wall(0, y)
            self.game_map.add_wall(self.game_map.width - 1, y)

        # Внутренние стены
        for x, y in [(5, 5), (5, 6), (15, 8), (15, 9), (10, 7), (10, 8), (7, 10), (8, 10), (12, 3), (13, 3)]:
            self.game_map.add_wall(x, y)

    def update_projectiles(self):
        for proj in self.projectiles[:]:
            old_x, old_y = proj.x, proj.y
            proj.x += proj.dx
            proj.y += proj.dy
            proj.distance_traveled += 1

            # Эффект следа
            effect_color = self.PROJECTILE_COLORS.get(proj.spell.name, (255, 255, 0))
            trail_effect = VisualEffect(
                old_x, old_y,
                effect_color,
                duration=5,
                size=self.cell_size // 6
            )
            self.visual_effects.append(trail_effect)

            # Проверка коллизий
            if (not self.game_map.is_valid_position(int(proj.x), int(proj.y)) or
                    proj.distance_traveled > proj.spell.range):
                # Эффект взрыва
                explosion = VisualEffect(
                    proj.x, proj.y,
                    (255, 200, 0),
                    duration=10,
                    size=self.cell_size // 2
                )
                self.visual_effects.append(explosion)
                self.projectiles.remove(proj)
                continue

            # Попадание в волшебника
            for wizard in self.wizards:
                if (int(proj.x) == wizard.x and int(proj.y) == wizard.y and
                        wizard != proj.caster):
                    wizard.health -= proj.spell.damage
                    hit_effect = VisualEffect(
                        wizard.x, wizard.y,
                        (255, 0, 0),
                        duration=15,
                        size=self.cell_size // 2
                    )
                    self.visual_effects.append(hit_effect)
                    proj.caster.score += proj.spell.damage  # Счет

                    # Специальный эффект для молнии
                    if proj.spell.special_effect == "vision_reduce":
                        if random.random() < 0.5:
                            wizard.vision_range = max(1, wizard.vision_range // 2)

                    self.projectiles.remove(proj)

                    # Проверка на победу
                    if wizard.health <= 0:
                        self.game_over = True
                    break

    def handle_input(self):
        # No keyboard input for wizard movement - only strategy execution
        pass

    def move_wizard(self, wizard_name, dx, dy):
        for wizard in self.wizards:
            if wizard.name == wizard_name:
                new_x = wizard.x + dx
                new_y = wizard.y + dy
                if self.game_map.is_valid_position(new_x, new_y):
                    wizard.x = new_x
                    wizard.y = new_y
                    wizard.direction = (dx, dy)
                    return True
        return False

    def select_spell(self, wizard_name, spell_name):
        if spell_name not in self.spells:
            return False
        for wizard in self.wizards:
            if wizard.name == wizard_name:
                wizard.selected_spell = spell_name
                return True
        return False

    def toggle_ai(self):
        self.ai_enabled = not self.ai_enabled
        return f"AI {'enabled' if self.ai_enabled else 'disabled'}"

    def cast_current_spell(self):
        spell = self.spells[self.gandalf.selected_spell]

        if self.gandalf.mana >= spell.mana_cost:
            self.gandalf.mana -= spell.mana_cost
            self.projectiles.append(SpellProjectile(
                self.gandalf.x, self.gandalf.y,
                self.gandalf.direction[0], self.gandalf.direction[1],
                spell, self.gandalf
            ))
            # Реген маны
            self.regenerate_mana(self.gandalf, 5)

    def regenerate_mana(self, wizard, amount):
        wizard.mana = min(100, wizard.mana + amount)

    def cast_spell(self, wizard_name, spell_name, target_x, target_y):
        for wizard in self.wizards:
            if wizard.name == wizard_name:
                if spell_name in self.spells:
                    spell = self.spells[spell_name]
                    if wizard.mana >= spell.mana_cost:
                        wizard.mana -= spell.mana_cost

                        # Вычисление направления
                        dx = 0
                        dy = 0
                        if target_x > wizard.x:
                            dx = 1
                        elif target_x < wizard.x:
                            dx = -1
                        if target_y > wizard.y:
                            dy = 1
                        elif target_y < wizard.y:
                            dy = -1

                        wizard.direction = (dx, dy)

                        # Специальный эффект для молнии
                        if spell_name == "молния":
                            spell.special_effect = "vision_reduce"
                        else:
                            spell.special_effect = None

                        self.projectiles.append(SpellProjectile(
                            wizard.x, wizard.y,
                            dx, dy,
                            spell, wizard
                        ))
                        return True
                return False
        return False

    def load_strategy(self, wizard_name):
        try:
            filename = "gandelf_strategy.txt" if wizard_name == "Гэндальф" else "merlin_strategy.txt"
            with open(filename, 'r', encoding='utf-8') as f:
                commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                return commands
        except FileNotFoundError:
            print(f"Strategy file not found for {wizard_name}")
            return []
        except Exception as e:
            print(f"Error loading strategy for {wizard_name}: {e}")
            return []

    def execute_strategy(self, wizard_name):
        commands = self.load_strategy(wizard_name)
        if commands and self.strategy_counters[wizard_name] < len(commands):
            # Используем команду по текущему счетчику
            command = commands[self.strategy_counters[wizard_name]]

            try:
                from tokenize_and_parse import tokenize, parse
                from evaluate import evaluate

                tokens = tokenize(command)
                expression = parse(tokens)
                result = evaluate(expression, self.names)
                print(f"{wizard_name} executed: {command} -> {result}")

            except Exception as e:
                print(f"Error executing {wizard_name} command '{command}': {e}")

            # Увеличиваем счетчик для следующей команды
            self.strategy_counters[wizard_name] += 1

            # Если команды закончились, начинаем сначала
            if self.strategy_counters[wizard_name] >= len(commands):
                self.strategy_counters[wizard_name] = 0

    def handle_lisp_command(self):
        console = self.active_console

        if console["input"].strip() == "help":
            import lisp_manual
            console["output"] = lisp_manual.__doc__
            return
        elif console["input"].strip() == "clear":
            console["history"].clear()
            console["output"] = "История очищена"
            console["input"] = ""
            return
        elif console["input"].strip() == "history":
            console["output"] = "\n".join(console["history"])
            return

        try:
            tokens = tokenize(console["input"])
            expression = parse(tokens)
            result = evaluate(expression, self.names)
            console["output"] = str(result)
            if console["input"].strip():
                console["history"].append(console["input"])
            console["history_index"] = -1
            console["input"] = ""
        except Exception as e:
            console["output"] = f"Error: {str(e)}"

    def draw(self):
        self.screen.fill((255, 255, 255))

        if not self.game_started and self.countdown > 0:
            countdown_font = pygame.font.SysFont('Arial', 72)
            countdown_text = countdown_font.render(str(self.countdown), True, (255, 0, 0))
            self.screen.blit(countdown_text, (self.screen_width // 2 - countdown_text.get_width() // 2,
                                              self.screen_height // 2 - countdown_text.get_height() // 2))

        # Обновление эффектов
        for effect in self.visual_effects[:]:
            effect.current_frame += 1
            if effect.current_frame >= effect.duration:
                self.visual_effects.remove(effect)

        # Создание поля
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size,
                                   self.cell_size, self.cell_size)
                if self.game_map.is_wall(x, y):
                    pygame.draw.rect(self.screen, self.WALL_COLOR, rect)
                else:
                    pygame.draw.rect(self.screen, self.FLOOR_COLOR, rect)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

        # Создание эффектов
        for effect in self.visual_effects:
            x = int(effect.x * self.cell_size + self.cell_size // 2)
            y = int(effect.y * self.cell_size + self.cell_size // 2)
            alpha = 255 * (1 - effect.current_frame / effect.duration)
            surface = pygame.Surface((effect.size * 2, effect.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*effect.color, int(alpha)), (effect.size, effect.size), effect.size)
            self.screen.blit(surface, (x - effect.size, y - effect.size))

        for proj in self.projectiles:
            x = int(proj.x * self.cell_size + self.cell_size // 2)
            y = int(proj.y * self.cell_size + self.cell_size // 2)
            color = self.PROJECTILE_COLORS[proj.spell.name]
            pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 4)

        for wizard in self.wizards:
            x = wizard.x * self.cell_size + self.cell_size // 2
            y = wizard.y * self.cell_size + self.cell_size // 2

            # Отрисовка зоны видимости
            visible_cells = wizard.get_visible_cells(self.game_map)
            for vx, vy in visible_cells:
                cell_rect = pygame.Rect(vx * self.cell_size, vy * self.cell_size,
                                        self.cell_size, self.cell_size)
                vision_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                color = (*self.WIZARD_COLORS[wizard.name], 30)  # Полупрозрачный цвет
                pygame.draw.rect(vision_surface, color, vision_surface.get_rect())
                self.screen.blit(vision_surface, cell_rect)

            pygame.draw.circle(self.screen, self.WIZARD_COLORS[wizard.name], (x, y), self.cell_size // 3)

            end_x = x + wizard.direction[0] * self.cell_size // 2
            end_y = y + wizard.direction[1] * self.cell_size // 2
            pygame.draw.line(self.screen, (0, 0, 0), (x, y), (end_x, end_y), 2)

            name_text = self.font.render(f"{wizard.name} ({wizard.selected_spell})", True, (0, 0, 0))
            hp_text = self.font.render(f"HP: {wizard.health}", True, (0, 0, 0))
            mp_text = self.font.render(f"Мана: {wizard.mana}", True, (0, 0, 0))
            score_text = self.font.render(f"Счет: {wizard.score}", True, (0, 0, 0))

            self.screen.blit(name_text, (x - 40, y - 40))
            self.screen.blit(hp_text, (x - 20, y + 5))
            self.screen.blit(mp_text, (x - 20, y + 20))
            self.screen.blit(score_text, (x - 20, y + 35))

        # Removed console UI

        # Draw active console output
        output_lines = []
        words = self.active_console["output"].split()
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.console_font.size(test_line)[0] < self.screen_width - 20:
                current_line = test_line
            else:
                output_lines.append(current_line)
                current_line = word
        if current_line:
            output_lines.append(current_line)

        for i, line in enumerate(output_lines[-2:]):  # Show last 2 lines
            output_text = self.console_font.render(line.strip(), True, (200, 200, 200))
            self.screen.blit(output_text, (15, self.game_map.height * self.cell_size + 50 + i * 20))

        if self.game_over:
            winner = None
            for wizard in self.wizards:
                if wizard.health > 0:
                    winner = wizard

            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))

            game_over_font = pygame.font.SysFont('Arial', 48)
            game_over_text = game_over_font.render("ИГРА ОКОНЧЕНА", True, (255, 0, 0))

            if winner:
                winner_text = game_over_font.render(f"Победитель: {winner.name}", True, (255, 255, 0))
                score_text = self.font.render(f"Счет: {winner.score}", True, (255, 255, 255))

                self.screen.blit(game_over_text, (self.screen_width // 2 - game_over_text.get_width() // 2,
                                                  self.screen_height // 2 - 80))
                self.screen.blit(winner_text, (self.screen_width // 2 - winner_text.get_width() // 2,
                                               self.screen_height // 2 - 20))
                self.screen.blit(score_text, (self.screen_width // 2 - score_text.get_width() // 2,
                                              self.screen_height // 2 + 40))
            else:
                draw_text = game_over_font.render("Ничья!", True, (255, 255, 0))
                self.screen.blit(game_over_text, (self.screen_width // 2 - game_over_text.get_width() // 2,
                                                  self.screen_height // 2 - 50))
                self.screen.blit(draw_text, (self.screen_width // 2 - draw_text.get_width() // 2,
                                             self.screen_height // 2 + 10))

        if self.show_help:
            help_surface = pygame.Surface((self.screen_width - 100, self.screen_height - 150), pygame.SRCALPHA)
            help_surface.fill((50, 50, 50, 220))
            self.screen.blit(help_surface, (50, 50))

            help_title = pygame.font.SysFont('Arial', 24).render("ПОМОЩЬ", True, (255, 255, 0))
            self.screen.blit(help_title, (self.screen_width // 2 - help_title.get_width() // 2, 70))

            help_lines = [
                "Движение: стрелки (←↑→↓)",
                "Выбор заклинания: 1 - огненный шар, 2 - ледяной осколок, 3 - молния",
                "Применение заклинания: Пробел",
                "LISP команды:",
                "  (move-wizard \"Гэндальф\" (1 0)) - переместить волшебника вправо",
                "  (cast-spell \"Гэндальф\" \"fireball\" 10 5) - применить заклинание в координаты",
                "F1 - показать/скрыть помощь",
                "ESC - выход из игры"
            ]

            y_pos = 110
            for line in help_lines:
                help_text = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(help_text, (70, y_pos))
                y_pos += 30

        pygame.display.flip()

    def run(self):
        ai_timer = 0

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_F1:
                        self.show_help = not self.show_help
                    elif event.key == pygame.K_SPACE:
                        # Проверяем, активна ли консоль
                        mouse_pos = pygame.mouse.get_pos()
                        console_area = pygame.Rect(0, self.game_map.height * self.cell_size,
                                                   self.screen_width, 120)
                        if console_area.collidepoint(mouse_pos):
                            self.lisp_command_input += " "
                        elif not self.game_over:
                            self.cast_current_spell()
                    elif event.key == pygame.K_RETURN:
                        if self.active_console["input"].strip():
                            self.handle_lisp_command()
                    elif event.key == pygame.K_BACKSPACE:
                        self.active_console["input"] = self.active_console["input"][:-1]
                    elif event.key == pygame.K_UP and self.active_console["history"]:
                        if self.active_console["history_index"] < len(self.active_console["history"]) - 1:
                            self.active_console["history_index"] += 1
                            self.active_console["input"] = self.active_console["history"][
                                -(self.active_console["history_index"] + 1)]
                    elif event.key == pygame.K_DOWN and self.active_console["history_index"] > -1:
                        self.active_console["history_index"] -= 1
                        if self.active_console["history_index"] == -1:
                            self.active_console["input"] = ""
                        else:
                            self.active_console["input"] = self.active_console["history"][
                                -(self.active_console["history_index"] + 1)]
                    elif event.key == pygame.K_TAB:
                        # Switch between consoles
                        self.active_console = self.merlin_console if self.active_console == self.gandalf_console else self.gandalf_console
                    elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        try:
                            import tkinter as tk
                            root = tk.Tk()
                            root.withdraw()
                            clipboard_text = root.clipboard_get()
                            root.destroy()
                            self.active_console["input"] += clipboard_text
                        except:
                            pass
                    else:
                        if event.unicode and event.unicode.isprintable():
                            self.active_console["input"] += event.unicode

            if not self.game_over:
                if not self.game_started:
                    self.countdown_timer += 1
                    if self.countdown_timer >= 30:  # 30 кадров = 1 секунда
                        self.countdown_timer = 0
                        self.countdown -= 1
                        if self.countdown <= 0:
                            self.game_started = True
                            self.ai_enabled = True  # Автоматически включаем ИИ
                else:
                    ai_timer += 1
                    if ai_timer >= 30:  # Выполняем команды каждую секунду
                        ai_timer = 0
                        self.execute_strategy("Гэндальф")
                        self.execute_strategy("Мерлин")

                self.update_projectiles()

                # Регенерация маны для обоих волшебников
                self.regenerate_mana(self.gandalf, 0.5)
                self.regenerate_mana(self.merlin, 0.5)

            self.draw()
            self.clock.tick(30)

        pygame.quit()