# nil = () ≈ None
# (a . b)  ≈ (a, b)
# (1 2 3)   = (1 . (2 . (3 . ())))
# (1 2 . 3) = (1 . (2 . 3))

# nil = ()
# def pair(a, b):
#    return (a, b)

# (1, 2) → "(1 . 2)"
# (1, (2, 3)) → "(1 . (2 . 3))"
# ("a, b", "c") → ("a . b" . "c")

def is_pair(obj) -> bool:
    if type(obj) == tuple and len(obj) == 2:
        return True
    return False


# ((((0 . 1) . 2) . 3) . 4)

def print_pair(pair):
    print("(", end='')
    if is_pair(pair[0]):
        print_pair(pair[0])
    else:
        print(pair[0], end='')
    print(" . ", end="")
    if is_pair(pair[1]):
        print_pair(pair[1])
    else:
        print(pair[1], end='')
    print(")")


# ДЗ 1: print_list((1, (2, (3, ())))) → "(1 2 3)"

# (+ 1 2 3) → 6     # (+ . (1 . (2 . (3 . ()))))
#                          ^^^^^^^^^^^^^^^^^^^^
# (* 4 5 6) → 120
# (- 3 2)   → 1

# (+)       → 0
# (*)       → 1

# (* 4 5 6 7) → (* (* 4 5) (* 6) (* 7)) → (* (* 4 5 6 7) (*))

# tail vvvvvvvvvvvvvv
# (1 . (2 . (3 . ())))
#  ^ head

def add(pair):
    if pair == ():
        return 0
    else:
        head, tail = pair
        return head + add(tail)


# add((1 2 3)) = 1 + add((2 3)) = 1 + (2 + add((3))) = 1 + (2 + (3 + add(()))) = 1 + (2 + (3 + 0)) = 1 + 2 + 3 = 6

# ДЗ 2: функция умножения, (*)

# (- 3 2)   → 1
# (- 1 2 3) → некорректно!

# (3 . (2 . ()))
def sub(pair):
    head, tail = pair
    return head - tail[0]


# ДЗ 3: функция деления, (/)

# nil               ≈ False
# что угодно другое ≈ True

# (> 1 2) → nil
# (> 2 1) → 1
def greater_than(pair):
    head, tail = pair
    arg2 = tail[0]
    if head > arg2:
        return 1
    return ()


# ДЗ 4: функции <, <=, >=, =

# (+ 1 (* 2 3)) → 7
# (+ 1 6      ) → 7
def evaluate(obj):
    return obj

# (cond
#   ((> a b) 1)
#   ((< a b) -1)
#   (1 0))

# ↓

# if a > b: return 1
# elif a < b: return -1
# else: return 0

# (cond) → nil

# ДЗ 5*: написать функцию cond