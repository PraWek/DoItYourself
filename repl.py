from tokenize_and_parse import tokenize, parse
from evaluate import evaluate
from all_namespace import namespace

names = namespace()


def lisp_to_list(values):
    return values


def print_value(value):
    if value is None:
        print("nil")
    else:
        print(value)


def repl():
    while True:
        try:
            line = input("> ")
            if not line.strip():
                continue

            try:
                tokens = tokenize(line)
            except Exception as e:
                print(f"Tokenization error: {e}")
                continue

            try:
                values = parse(tokens)
            except SyntaxError as e:
                print(f"Syntax error: {e}")
                continue
            except Exception as e:
                print(f"Parse error: {e}")
                continue

            try:
                for value in lisp_to_list(values):
                    result = evaluate(value, names)
                    print_value(result)
            except NameError as e:
                print(f"Symbol error: {e}")
            except TypeError as e:
                print(f"Type error: {e}")
            except ValueError as e:
                print(f"Value error: {e}")
            except ZeroDivisionError:
                print("Division by zero")
            except Exception as e:
                print(f"Evaluation error: {e}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    repl()
