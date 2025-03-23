from pathlib import Path

from lisp import LispSyntaxError, parse_many

from .model import SPELLS, WizardGame
from .scripting import GameSession


HELP = """Команды дуэли:
  (move dx dy)
  (select-spell "название")
  (cast "название" x y)

Сведения о бое:
  (health)  (mana)  (position)
  (enemy-health)  (enemy-position)  (distance)  (visible?)

Можно использовать define, lambda, let, if, cond и остальные формы Lisp.
Вне Lisp: help, state, load ПУТЬ, restart, quit.
"""


def status(game):
    lines = [game.board(), ""]
    for wizard in game.wizards:
        marker = "*" if wizard is game.active_wizard and not game.game_over else " "
        lines.append(
            f"{marker} {wizard.name}: HP {max(0, wizard.health):3}  MP {wizard.mana:3}  "
            f"{wizard.selected_spell}  ({wizard.x}, {wizard.y})"
        )
    lines.append(f"Ход {game.turn}: {game.active_wizard.name}")
    return "\n".join(lines)


def read_expression(prompt):
    lines = [input(prompt)]
    while True:
        source = "\n".join(lines).strip()
        if source in {"help", "state", "restart", "quit", "exit"} or source.startswith("load "):
            return source
        try:
            parse_many(source)
            return source
        except LispSyntaxError as error:
            if "Отсутствует закрывающая" not in str(error) and "Неожиданный конец" not in str(error):
                return source
            lines.append(input("... "))


def run():
    session = GameSession()
    print("БИТВА МАГОВ — Lisp-терминал")
    print('Введите "help", чтобы увидеть команды.\n')
    print(status(session.game))

    while not session.game.game_over:
        try:
            source = read_expression(f"\n{session.game.active_wizard.name}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо следующей дуэли.")
            return
        if not source:
            continue
        if source == "help":
            print(HELP)
            print("Заклинания:")
            for spell in SPELLS.values():
                print(f"  {spell.name}: урон {spell.damage}, мана {spell.mana_cost}, дальность {spell.range}")
            continue
        if source == "state":
            print(status(session.game))
            continue
        if source.startswith("load "):
            path = Path(source[5:].strip().strip('"'))
            try:
                result = session.execute(path.read_text(encoding="utf-8"))
                print(session.format_result(result))
            except OSError as error:
                print(f"Ошибка: {error}")
            continue
        if source == "restart":
            session = GameSession(WizardGame())
            print(status(session.game))
            continue
        if source in {"quit", "exit"}:
            print("До следующей дуэли.")
            return

        result = session.execute(source)
        print(session.format_result(result))
        if result.action_used:
            print(status(session.game))

    winner = session.game.winner
    print(f"\nПобедитель: {winner.name}" if winner else "\nНичья")


if __name__ == "__main__":
    run()
