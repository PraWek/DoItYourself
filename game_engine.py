import pygame
from typing import List, Tuple, Dict
from all_namespace import namespace


class Wizard:
    def __init__(self, x: int, y: int, name: str):
        self.x = x
        self.y = y
        self.name = name
        self.health = 100
        self.mana = 100
        self.direction = (0, 1)  # Направление взгляда (dx, dy)
        self.selected_spell = "fireball"


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
        self.current_wizard_index = None
        self.game_map = GameMap(20, 15)  # Увеличенное поле
        self.wizards: List[Wizard] = []
        self.casting_mode = False
        self.visual_effects: List[VisualEffect] = []
        self.spells: Dict[str, Spell] = {
            "fireball": Spell("fireball", 30, 20, 5),
            "ice_shard": Spell("ice_shard", 20, 15, 4),
            "lightning": Spell("lightning", 40, 35, 6)
        }
        self.projectiles: List[SpellProjectile] = []
        self.names = namespace()

        # Добавляем волшебников
        self.gandalf = Wizard(16, 11, "Гэндальф")
        self.merlin = Wizard(3, 3, "Мерлин")
        self.wizards = [self.gandalf, self.merlin]
        self.enemy = self.merlin  # Мерлин теперь противник

        pygame.init()
        self.cell_size = 40
        self.screen_width = self.game_map.width * self.cell_size
        self.screen_height = self.game_map.height * self.cell_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Битва Волшебников")

        self.font = pygame.font.SysFont('Arial', 16)

        self.WALL_COLOR = (100, 100, 100)
        self.FLOOR_COLOR = (200, 200, 200)
        self.WIZARD_COLORS = {
            "Гэндальф": (255, 0, 0),  # Красный для Гэндальфа
            "Мерлин": (0, 0, 255)  # Синий для Мерлина
        }
        self.PROJECTILE_COLORS = {
            "fireball": (255, 100, 0),
            "ice_shard": (0, 255, 255),
            "lightning": (255, 255, 0)
        }

        self._setup_game()
        self.clock = pygame.time.Clock()
        self.running = True

    def _setup_game(self):
        # Добавляем стены по краям
        for x in range(self.game_map.width):
            self.game_map.add_wall(x, 0)
            self.game_map.add_wall(x, self.game_map.height - 1)
        for y in range(self.game_map.height):
            self.game_map.add_wall(0, y)
            self.game_map.add_wall(self.game_map.width - 1, y)

        # Добавляем внутренние стены
        for x, y in [(5, 5), (5, 6), (15, 8), (15, 9), (10, 7), (10, 8)]:
            self.game_map.add_wall(x, y)

        # Добавляем волшебников
        self.wizards.append(Wizard(3, 3, "Мерлин"))
        self.wizards.append(Wizard(16, 11, "Гэндальф"))

    def update_projectiles(self):
        for proj in self.projectiles[:]:
            old_x, old_y = proj.x, proj.y
            proj.x += proj.dx
            proj.y += proj.dy
            proj.distance_traveled += 1

            # Добавляем эффект следа
            effect_color = self.PROJECTILE_COLORS.get(proj.spell.name, (255, 255, 0))
            trail_effect = VisualEffect(
                old_x, old_y,
                effect_color,
                duration=5,
                size=self.cell_size // 6
            )
            self.visual_effects.append(trail_effect)

            # Проверяем столкновения
            if (not self.game_map.is_valid_position(int(proj.x), int(proj.y)) or
                    proj.distance_traveled > proj.spell.range):
                # Добавляем эффект взрыва
                explosion = VisualEffect(
                    proj.x, proj.y,
                    (255, 200, 0),
                    duration=10,
                    size=self.cell_size // 2
                )
                self.visual_effects.append(explosion)
                self.projectiles.remove(proj)
                continue

            # Проверяем попадание в волшебника
            for wizard in self.wizards:
                if (int(proj.x) == wizard.x and int(proj.y) == wizard.y and
                        wizard == self.merlin):  # Проверяем попадание только в Мерлина
                    wizard.health -= proj.spell.damage
                    self.projectiles.remove(proj)
                    break

    def handle_input(self):
        keys = pygame.key.get_pressed()
        wizard = self.wizards[self.current_wizard_index]

        if not self.casting_mode:
            # Движение
            if keys[pygame.K_LEFT]:
                if self.game_map.is_valid_position(wizard.x - 1, wizard.y):
                    wizard.x -= 1
                    wizard.direction = (-1, 0)
            if keys[pygame.K_RIGHT]:
                if self.game_map.is_valid_position(wizard.x + 1, wizard.y):
                    wizard.x += 1
                    wizard.direction = (1, 0)
            if keys[pygame.K_UP]:
                if self.game_map.is_valid_position(wizard.x, wizard.y - 1):
                    wizard.y -= 1
                    wizard.direction = (0, -1)
            if keys[pygame.K_DOWN]:
                if self.game_map.is_valid_position(wizard.x, wizard.y + 1):
                    wizard.y += 1
                    wizard.direction = (0, 1)

            # Выбор заклинания
            if keys[pygame.K_1]:
                wizard.selected_spell = "fireball"
            if keys[pygame.K_2]:
                wizard.selected_spell = "ice_shard"
            if keys[pygame.K_3]:
                wizard.selected_spell = "lightning"

    def cast_current_spell(self):
        spell = self.spells[self.gandalf.selected_spell]

        if self.gandalf.mana >= spell.mana_cost:
            self.gandalf.mana -= spell.mana_cost
            self.projectiles.append(SpellProjectile(
                self.gandalf.x, self.gandalf.y,
                self.gandalf.direction[0], self.gandalf.direction[1],
                spell, self.gandalf
            ))

    def draw(self):
        self.screen.fill((255, 255, 255))

        # Обновляем визуальные эффекты
        for effect in self.visual_effects[:]:
            effect.current_frame += 1
            if effect.current_frame >= effect.duration:
                self.visual_effects.remove(effect)

        # Отрисовка поля
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size,
                                   self.cell_size, self.cell_size)
                if self.game_map.is_wall(x, y):
                    pygame.draw.rect(self.screen, self.WALL_COLOR, rect)
                else:
                    pygame.draw.rect(self.screen, self.FLOOR_COLOR, rect)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

        # Отрисовка визуальных эффектов
        for effect in self.visual_effects:
            x = int(effect.x * self.cell_size + self.cell_size // 2)
            y = int(effect.y * self.cell_size + self.cell_size // 2)
            alpha = 255 * (1 - effect.current_frame / effect.duration)
            surface = pygame.Surface((effect.size * 2, effect.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*effect.color, alpha), (effect.size, effect.size), effect.size)
            self.screen.blit(surface, (x - effect.size, y - effect.size))

        # Отрисовка снарядов
        for proj in self.projectiles:
            x = int(proj.x * self.cell_size + self.cell_size // 2)
            y = int(proj.y * self.cell_size + self.cell_size // 2)
            color = self.PROJECTILE_COLORS[proj.spell.name]
            pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 4)

        # Отрисовка волшебников
        for i, wizard in enumerate(self.wizards):
            x = wizard.x * self.cell_size + self.cell_size // 2
            y = wizard.y * self.cell_size + self.cell_size // 2

            # Круг для волшебника
            pygame.draw.circle(self.screen, self.WIZARD_COLORS[wizard.name], (x, y), self.cell_size // 3)

            # Направление взгляда
            end_x = x + wizard.direction[0] * self.cell_size // 2
            end_y = y + wizard.direction[1] * self.cell_size // 2
            pygame.draw.line(self.screen, (0, 0, 0), (x, y), (end_x, end_y), 2)

            # Информация о волшебнике
            name_text = self.font.render(f"{wizard.name} ({wizard.selected_spell})", True, (0, 0, 0))
            hp_text = self.font.render(f"HP: {wizard.health}", True, (0, 0, 0))
            mp_text = self.font.render(f"MP: {wizard.mana}", True, (0, 0, 0))

            self.screen.blit(name_text, (x - 40, y - 30))
            self.screen.blit(hp_text, (x - 20, y + 5))
            self.screen.blit(mp_text, (x - 20, y + 20))

        pygame.display.flip()

    def get_game_state(self):
        state = "Состояние игры:\n"
        state += f"Текущий ход: {self.wizards[self.current_wizard_index].name}\n"
        for wizard in self.wizards:
            state += f"\n{wizard.name}:\n"
            state += f"  Позиция: ({wizard.x}, {wizard.y})\n"
            state += f"  Здоровье: {wizard.health}\n"
            state += f"  Мана: {wizard.mana}\n"
            state += f"  Выбранное заклинание: {wizard.selected_spell}\n"
        return state

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.gandalf.selected_spell = "огненный_шар"
                    elif event.key == pygame.K_2:
                        self.gandalf.selected_spell = "ледяной_осколок"
                    elif event.key == pygame.K_3:
                        self.gandalf.selected_spell = "молния"
                    elif event.key == pygame.K_SPACE:
                        self.cast_current_spell()

            # Обработка движения
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and self.game_map.is_valid_position(self.gandalf.x - 1, self.gandalf.y):
                self.gandalf.x -= 1
                self.gandalf.direction = (-1, 0)
            if keys[pygame.K_RIGHT] and self.game_map.is_valid_position(self.gandalf.x + 1, self.gandalf.y):
                self.gandalf.x += 1
                self.gandalf.direction = (1, 0)
            if keys[pygame.K_UP] and self.game_map.is_valid_position(self.gandalf.x, self.gandalf.y - 1):
                self.gandalf.y -= 1
                self.gandalf.direction = (0, -1)
            if keys[pygame.K_DOWN] and self.game_map.is_valid_position(self.gandalf.x, self.gandalf.y + 1):
                self.gandalf.y += 1
                self.gandalf.direction = (0, 1)

            self.update_projectiles()
            self.draw()
            self.clock.tick(30)

        pygame.quit()

