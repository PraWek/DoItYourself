from game_engine import GameEngine


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║     CYBERHACK TERMINAL v1.0                                       ║
║     Введите "help" для получения информации о доступных командах  ║
║     Введите "missions", чтобы просмотреть сценарии                ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def print_help():
    print("""
Доступные команды:
- missions : Список доступных хакерских миссий
- start N : Номер начальной миссии N
- clear   : Очистить терминал
- exit    : Выйти из терминала
    """)


def repl():
    game = GameEngine()
    print_banner()

    while True:
        try:
            line = input("hack> ").strip()

            if not line:
                continue

            if line == "help":
                print_help()
                continue

            if line == "missions":
                for i, scenario in enumerate(game.scenarios):
                    status = "✓" if scenario.completed else " "
                    print(f"[{i}] [{status}] {scenario.name}")
                continue

            if line.startswith("start "):
                try:
                    index = int(line.split()[1])
                    print(game.start_scenario(index))
                except (IndexError, ValueError):
                    print("Неверный номер миссии")
                continue

            if line == "clear":
                print("\n" * 50)
                print_banner()
                continue

            if line == "exit":
                print("Disconnecting from terminal...")
                break

            result = game.evaluate_code(line)
            print(result)

        except KeyboardInterrupt:
            print("\nDisconnecting from terminal...")
            break
        except EOFError:
            print("\nConnection lost.")
            break


if __name__ == "__main__":
    repl()
