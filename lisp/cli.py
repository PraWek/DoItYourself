from .errors import LispSyntaxError
from .interpreter import Interpreter
from .parser import parse_many


def read_expression(prompt="lisp> "):
    lines = [input(prompt)]
    while True:
        source = "\n".join(lines).strip()
        if source in {"quit", "exit"}:
            return source
        try:
            parse_many(source)
            return source
        except LispSyntaxError as error:
            if "Отсутствует закрывающая" not in str(error) and "Неожиданный конец" not in str(error):
                return source
            lines.append(input("... "))


def run():
    interpreter = Interpreter()
    print("Небольшой Lisp. Для выхода: quit")
    while True:
        try:
            source = read_expression()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if source in {"quit", "exit"}:
            return
        if not source:
            continue
        try:
            print(interpreter.format(interpreter.execute(source)))
        except Exception as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    run()
