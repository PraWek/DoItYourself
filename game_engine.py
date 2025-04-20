import pygame
from typing import List, Tuple, Dict
from all_namespace import namespace, create_move_wizard, cast_spell, create_select_spell, create_toggle_ai
from tokenize_and_parse import tokenize, parse
from evaluate import evaluate


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


class Spell:
    def __init__(self, name: str, damage: int, mana_cost: int, range: int):
        self.name = name
        self.damage = damage
        self.mana_cost = mana_cost
        self.range = range


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
        self.names[0]["move-wizard"] = {"function": create_move_wizard(self)}
        self.names[0]["select-spell"] = {"function": create_select_spell(self)}
        self.names[0]["toggle-ai"] = {"function": create_toggle_ai(self)}
        self.lisp_command_input = ""
        self.lisp_output = ""
        self.command_history = []
        self.history_index = -1
        self.show_help = False
        self.game_over = False

        # Add wizards
        self.gandalf = Wizard(16, 11, "Гэндальф")
        self.merlin = Wizard(3, 3, "Мерлин")
        self.wizards = [self.gandalf, self.merlin]
        self.current_wizard = self.gandalf

        pygame.init()
        self.cell_size = 40
        self.screen_width = self.game_map.width * self.cell_size
        self.screen_height = self.game_map.height * self.cell_size + 100  # Extra space for LISP console
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
                    self.projectiles.remove(proj)

                    # Проверка на победу
                    if wizard.health <= 0:
                        self.game_over = True
                    break

    def handle_input(self):
        # All input is now handled through LISP console commands
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

                        self.projectiles.append(SpellProjectile(
                            wizard.x, wizard.y,
                            dx, dy,
                            spell, wizard
                        ))
                        return True
                return False
        return False

    def handle_lisp_command(self):
        if self.lisp_command_input.strip() == "help":
            import lisp_manual
            self.lisp_output = lisp_manual.__doc__
            return
        elif self.lisp_command_input.strip() == "clear":
            self.command_history.clear()
            self.lisp_output = "История очищена"
            self.lisp_command_input = ""
            return
        elif self.lisp_command_input.strip() == "history":
            self.lisp_output = "\n".join(self.command_history)
            return

        try:
            tokens = tokenize(self.lisp_command_input)
            expression = parse(tokens)
            result = evaluate(expression, self.names)
            self.lisp_output = str(result)
            if self.lisp_command_input.strip():
                self.command_history.append(self.lisp_command_input)
            self.history_index = -1
            self.lisp_command_input = ""
        except Exception as e:
            self.lisp_output = f"Error: {str(e)}"

    def draw(self):
        self.screen.fill((255, 255, 255))

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

        # Создание снарядов
        for proj in self.projectiles:
            x = int(proj.x * self.cell_size + self.cell_size // 2)
            y = int(proj.y * self.cell_size + self.cell_size // 2)
            color = self.PROJECTILE_COLORS[proj.spell.name]
            pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 4)

        # Создание волшебников
        for wizard in self.wizards:
            x = wizard.x * self.cell_size + self.cell_size // 2
            y = wizard.y * self.cell_size + self.cell_size // 2

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

        # LISP Console background
        console_rect = pygame.Rect(0, self.game_map.height * self.cell_size,
                                   self.screen_width, 120)
        pygame.draw.rect(self.screen, (30, 30, 30), console_rect)

        # Input area
        input_rect = pygame.Rect(10, self.game_map.height * self.cell_size + 10,
                                 self.screen_width - 20, 30)
        pygame.draw.rect(self.screen, (50, 50, 50), input_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), input_rect, 1)

        # Prompt and input text
        prompt_text = self.console_font.render("LISP> ", True, (0, 255, 0))
        self.screen.blit(prompt_text, (15, self.game_map.height * self.cell_size + 17))

        input_text = self.console_font.render(self.lisp_command_input, True, (255, 255, 255))
        self.screen.blit(input_text, (65, self.game_map.height * self.cell_size + 17))

        # Help hint
        help_text = self.console_font.render("Введите 'help' для справки", True, (100, 100, 100))
        self.screen.blit(help_text, (self.screen_width - 200, self.game_map.height * self.cell_size + 17))

        # Output area with word wrap
        output_lines = []
        words = self.lisp_output.split()
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

        # Draw help if needed
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

    def ai_move(self):
        # Простой ИИ для вражеского волшебника

        self.regenerate_mana(self.merlin, 5)

        # Если Гэндальф находится в поле зрения, а у Мерлина достаточно маны, кастуется заклинание
        dx = self.gandalf.x - self.merlin.x
        dy = self.gandalf.y - self.merlin.y

        # На одной ли линии волшебники
        if (dx == 0 or dy == 0 or abs(dx) == abs(dy)) and self.merlin.mana >= 20:
            if dx != 0:
                dx = dx // abs(dx)
            if dy != 0:
                dy = dy // abs(dy)

            x, y = self.merlin.x, self.merlin.y
            path_clear = True

            while (x != self.gandalf.x or y != self.gandalf.y) and path_clear:
                x += dx
                y += dy
                if self.game_map.is_wall(x, y) and (x != self.gandalf.x or y != self.gandalf.y):
                    path_clear = False

            if path_clear:
                self.merlin.direction = (dx, dy)
                # Выбор заклинания в зависимости от расстояния
                distance = max(abs(self.gandalf.x - self.merlin.x), abs(self.gandalf.y - self.merlin.y))

                if distance <= 3:
                    self.merlin.selected_spell = "ледяной осколок"
                elif distance <= 5:
                    self.merlin.selected_spell = "огненный шар"
                else:
                    self.merlin.selected_spell = "молния"

                # Есть ли мана
                spell = self.spells[self.merlin.selected_spell]
                if self.merlin.mana >= spell.mana_cost:
                    self.merlin.mana -= spell.mana_cost
                    self.projectiles.append(SpellProjectile(
                        self.merlin.x, self.merlin.y,
                        dx, dy,
                        spell, self.merlin
                    ))
                return

        # В противном случае бежим к Гэндальфу
        possible_moves = []

        # Рассмотрим все соседние ячейки
        for move_dx, move_dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_y = self.merlin.x + move_dx, self.merlin.y + move_dy

            if self.game_map.is_valid_position(new_x, new_y):
                # Рассчитаем расстояние до Гэндальфа после перемещения
                distance = abs(new_x - self.gandalf.x) + abs(new_y - self.gandalf.y)
                possible_moves.append((move_dx, move_dy, distance))

        if possible_moves:
            possible_moves.sort(key=lambda x: x[2])

            # 30%-ная вероятность сделать случайный ход для обеспечения непредсказуемости
            import random
            if random.random() < 0.3:
                move_dx, move_dy, _ = random.choice(possible_moves)
            else:
                move_dx, move_dy, _ = possible_moves[0]

            self.merlin.x += move_dx
            self.merlin.y += move_dy
            self.merlin.direction = (move_dx, move_dy)

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
                        if self.lisp_command_input.strip():
                            self.handle_lisp_command()
                    elif event.key == pygame.K_BACKSPACE:
                        self.lisp_command_input = self.lisp_command_input[:-1]
                    elif event.key == pygame.K_UP and self.command_history:
                        if self.history_index < len(self.command_history) - 1:
                            self.history_index += 1
                            self.lisp_command_input = self.command_history[-(self.history_index + 1)]
                    elif event.key == pygame.K_DOWN and self.history_index > -1:
                        self.history_index -= 1
                        if self.history_index == -1:
                            self.lisp_command_input = ""
                        else:
                            self.lisp_command_input = self.command_history[-(self.history_index + 1)]
                    elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        try:
                            import tkinter as tk
                            root = tk.Tk()
                            root.withdraw()
                            clipboard_text = root.clipboard_get()
                            root.destroy()
                            self.lisp_command_input += clipboard_text
                        except:
                            pass
                    else:
                        # Add character to LISP input
                        if event.unicode and event.unicode.isprintable():
                            self.lisp_command_input += event.unicode

            if not self.game_over:
                self.handle_input()

                ai_timer += 1
                if self.ai_enabled and ai_timer >= 30:
                    ai_timer = 0
                    self.ai_move()

                self.update_projectiles()

                self.regenerate_mana(self.gandalf, 0.1)

            self.draw()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    game = WizardGame()
    game.run()
