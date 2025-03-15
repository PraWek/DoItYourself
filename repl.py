from tokenize_and_parse import tokenize, parse
from evaluate import evaluate
from all_namespace import namespace

names = namespace()

def lisp_to_list(values):
    return values

def print_value(value):
    print(value)

def repl():
    names = [{}]
    while True:
        try:
            line = input("> ")
            tokens = tokenize(line)
            values = parse(tokens)
            for value in lisp_to_list(values):
                print_value(evaluate(value, names))
        except (SyntaxError, ValueError, NameError, TypeError, SystemError) as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    repl()