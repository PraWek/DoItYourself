from calculation_functions import add, subtract, multiply, divide
from comparison_functions import less_than, greater_than, less_or_equal, greater_or_equal, equal
from evaluate import evaluate
import random as python_random


def try_function(args):
    names = namespace()
    if not args or len(args) < 2:
        raise ValueError("try требует минимум два аргумента")
    expr, handler = args[0], args[1]
    try:
        return evaluate(expr, names)
    except Exception as e:
        return evaluate((handler, (str(e), ())), names)


def create_move_wizard(game_instance):
    def move_wizard(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
            return "Неверные аргументы"
        wizard_name = args[0]
        move_coords = args[1]
        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Неверное имя волшебника"
        if isinstance(move_coords, tuple) and len(move_coords) == 2:
            dx, dy = move_coords
        elif isinstance(move_coords, (int, float)):
            if len(args) >= 3:
                dx, dy = move_coords, args[2]
            else:
                return "Неверные координаты движения"
        else:
            return "Неверные координаты движения"
        for wizard in game_instance.wizards:
            if wizard.name == wizard_name["value"]:
                if game_instance.game_map.is_valid_position(wizard.x + dx, wizard.y + dy):
                    wizard.x += dx
                    wizard.y += dy
                    wizard.direction = (dx, dy)
                    return True
        return False

    return move_wizard


def cast_spell(game_instance):
    def spell_handler(args):
        if not args or not isinstance(args, tuple) or len(args) < 2:
            return "Неверные аргументы"
        if len(args) == 3:
            wizard_name, spell_name, target_coords = args
            if isinstance(target_coords, tuple) and len(target_coords) == 2:
                target_x, target_y = target_coords
            else:
                return "Неверные координаты цели"
        elif len(args) == 4:
            wizard_name, spell_name, target_x, target_y = args
        else:
            return "Неверное количество аргументов"
        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Неверное имя волшебника"
        if not isinstance(spell_name, dict) or spell_name.get("type") != "string":
            return "Неверное имя заклинания"
        return game_instance.cast_spell(wizard_name["value"], spell_name["value"], target_x, target_y)

    return spell_handler


def create_select_spell(game_instance):
    def spell_handler(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
            return "Неверные аргументы"
        wizard_name = args[0]
        spell_name = args[1]
        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Неверное имя волшебника"
        if not isinstance(spell_name, dict) or spell_name.get("type") != "string":
            return "Неверное имя заклинания"
        return game_instance.select_spell(wizard_name["value"], spell_name["value"])

    return spell_handler


def create_toggle_ai(game_instance):
    def toggle_handler(_):
        return game_instance.toggle_ai()

    return toggle_handler


def create_get_wizard_health(game_instance):
    def get_health(args):
        if not args or not isinstance(args, tuple) or len(args) != 1:
            return 0
        wizard_name = args[0]
        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return 0
        for wizard in game_instance.wizards:
            if wizard.name == wizard_name["value"]:
                return wizard.health
        return 0

    return get_health


def create_is_wizard_visible(game_instance):
    def is_visible(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
            return False
        observer_name = args[0]
        target_name = args[1]
        if not isinstance(observer_name, dict) or observer_name.get("type") != "string":
            return False
        if not isinstance(target_name, dict) or target_name.get("type") != "string":
            return False
        observer = None
        target = None
        for wizard in game_instance.wizards:
            if wizard.name == observer_name["value"]:
                observer = wizard
            elif wizard.name == target_name["value"]:
                target = wizard
        if not observer or not target:
            return False
        visible_cells = observer.get_visible_cells(game_instance.game_map)
        return (target.x, target.y) in visible_cells

    return is_visible


def create_get_distance(game_instance):
    def get_distance(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
            return 999
        wizard1_name = args[0]
        wizard2_name = args[1]
        if not isinstance(wizard1_name, dict) or wizard1_name.get("type") != "string":
            return 999
        if not isinstance(wizard2_name, dict) or wizard2_name.get("type") != "string":
            return 999
        wizard1 = None
        wizard2 = None
        for wizard in game_instance.wizards:
            if wizard.name == wizard1_name["value"]:
                wizard1 = wizard
            elif wizard.name == wizard2_name["value"]:
                wizard2 = wizard
        if not wizard1 or not wizard2:
            return 999
        return abs(wizard1.x - wizard2.x) + abs(wizard1.y - wizard2.y)

    return get_distance


def random_function(args):
    if not args:
        return python_random.random()
    if len(args) == 1 and isinstance(args[0], (int, float)):
        return python_random.randint(0, int(args[0]) - 1)
    return python_random.random()


def mod_function(args):
    if len(args) != 2:
        raise ValueError("mod требует ровно 2 аргумента")
    return args[0] % args[1]


def if_function(args):
    if not args or not isinstance(args, tuple) or len(args) < 2:
        raise ValueError("if требует минимум 2 аргумента")
    condition = args[0]
    then_expr = args[1]
    else_expr = args[2] if len(args) > 2 else ()
    import inspect
    frame = inspect.currentframe()
    try:
        while frame:
            if 'names' in frame.f_locals:
                names = frame.f_locals['names']
                break
            frame = frame.f_back
        else:
            raise ValueError("Не удается найти пространство имен в контексте")
    finally:
        del frame
    condition_result = evaluate(condition, names)
    if condition_result and condition_result != ():
        return evaluate(then_expr, names)
    else:
        return evaluate(else_expr, names)


def progn_function(args):
    if not args:
        return ()
    import inspect
    frame = inspect.currentframe()
    try:
        while frame:
            if 'names' in frame.f_locals:
                names = frame.f_locals['names']
                break
            frame = frame.f_back
        else:
            raise ValueError("Не удается найти пространство имен в контексте")
    finally:
        del frame
    result = ()
    while args:
        if isinstance(args, tuple) and len(args) >= 2:
            result = evaluate(args[0], names)
            args = args[1]
        elif isinstance(args, tuple) and len(args) == 1:
            result = evaluate(args[0], names)
            break
        else:
            result = evaluate(args, names)
            break
    return result


def reduce_func(func, iterable, initializer=None):
    import functools
    if initializer is not None:
        return functools.reduce(func, iterable, initializer)
    else:
        return functools.reduce(func, iterable)


def cond_eval(clauses):
    for clause in clauses:
        if len(clause) >= 2:
            condition, action = clause[0], clause[1]
            if condition or condition == 't':
                return action
    return None


def let_eval(args):
    if len(args) < 2:
        return None
    from evaluate import evaluate
    bindings, body = args[0], args[1:]
    new_env = namespace()
    if isinstance(bindings, (list, tuple)):
        for binding in bindings:
            if isinstance(binding, (list, tuple)) and len(binding) >= 2:
                var_name = binding[0]
                var_value = evaluate(binding[1], new_env)
                new_env[0][var_name] = var_value
    result = None
    for expr in body:
        result = evaluate(expr, new_env)
    return result


def letrec_eval(args):
    if len(args) < 2:
        return None
    from evaluate import evaluate
    bindings, body = args[0], args[1:]
    new_env = namespace()
    if isinstance(bindings, (list, tuple)):
        for binding in bindings:
            if isinstance(binding, (list, tuple)) and len(binding) >= 2:
                var_name = binding[0]
                var_value = evaluate(binding[1], new_env)
                new_env[0][var_name] = var_value
    result = None
    for expr in body:
        result = evaluate(expr, new_env)
    return result


def create_lambda(args):
    if len(args) < 2:
        return lambda x: x
    params, body = args[0], args[1]
    return lambda x: body


def namespace():
    return [{
        "nil": {"type": "nil", "value": None},
        "t": {"type": "boolean", "value": True},
        "+": {"function": add},
        "-": {"function": subtract},
        "*": {"function": multiply},
        "/": {"function": divide},
        "<": {"function": less_than},
        ">": {"function": greater_than},
        "<=": {"function": less_or_equal},
        ">=": {"function": greater_or_equal},
        "=": {"function": equal},
        "try": {"function": try_function},
        "str": {"function": lambda x: str(x[0]) if x else ""},
        "and": {"function": lambda args: all(args) if args else False},
        "or": {"function": lambda args: any(args) if args else False},
        "not": {"function": lambda args: not args[0] if args else True},
        "if": {"macro": if_function},
        "cond": {"function": lambda args: cond_eval(args)},
        "progn": {"function": progn_function},
        "let": {"function": lambda args: let_eval(args)},
        "letrec": {"function": lambda args: letrec_eval(args)},
        "lambda": {"function": lambda args: create_lambda(args)},
        "list": {"function": lambda args: list(args) if args else []},
        "car": {"function": lambda args: args[0][0] if args and args[0] else None},
        "cdr": {"function": lambda args: args[0][1:] if args and args[0] else []},
        "cons": {"function": lambda args: [args[0]] + list(args[1]) if len(args) >= 2 else args},
        "length": {"function": lambda args: len(args[0]) if args and hasattr(args[0], '__len__') else 0},
        "map": {"function": lambda args: [args[0](x) for x in args[1]] if len(args) >= 2 else []},
        "filter": {"function": lambda args: [x for x in args[1] if args[0](x)] if len(args) >= 2 else []},
        "reduce": {"function": lambda args: reduce_func(args[0], args[1], args[2] if len(args) > 2 else None) if len(
            args) >= 2 else None},
        "min": {"function": lambda args: min(args) if args else 0},
        "max": {"function": lambda args: max(args) if args else 0},
        "abs": {"function": lambda args: abs(args[0]) if args else 0},
        "random": {"function": random_function},
        "mod": {"function": mod_function},
        "sqrt": {"function": lambda args: int(args[0] ** 0.5) if args else 0},
    }]


def create_conditional_move(game_instance):
    def conditional_move(args):
        if not args or len(args) < 3:
            return False

        condition, true_action, false_action = args[0], args[1], args[2]

        try:
            result = evaluate(condition, namespace())
            action = true_action if result else false_action
            return evaluate(action, namespace())
        except:
            return False

    return conditional_move


def create_move_wizard(game_instance):
    def move_handler(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
            return "Invalid arguments"

        wizard_name = args[0]
        movement = args[1]

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"

        if isinstance(movement, tuple) and len(movement) == 2:
            dx, dy = movement
        else:
            return "Invalid movement coordinates"

        return game_instance.move_wizard(wizard_name["value"], dx, dy)

    return move_handler


def create_strategy_selector(game_instance):
    def strategy_selector(args):
        if not args or len(args) < 2:
            return "aggressive"

        wizard_name = args[0]
        health_threshold = args[1] if len(args) > 1 else 50

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "defensive"

        for wizard in game_instance.wizards:
            if wizard.name == wizard_name["value"]:
                if wizard.health < health_threshold:
                    return "defensive"
                elif wizard.mana > 80:
                    return "aggressive"
                else:
                    return "balanced"
        return "balanced"

    return strategy_selector


def create_spell_optimizer(game_instance):
    def spell_optimizer(args):
        if not args or len(args) < 2:
            return "огненный шар"

        wizard_name = args[0]
        target_distance = args[1] if len(args) > 1 else 5

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "огненный шар"

        # Logic for optimal spell selection based on distance and mana
        if target_distance <= 3:
            return "ледяной осколок"  # Short range, low mana
        elif target_distance <= 5:
            return "огненный шар"  # Medium range, medium mana
        else:
            return "молния"  # Long range, high mana

    return spell_optimizer


def create_position_evaluator(game_instance):
    def position_evaluator(args):
        if not args or len(args) < 3:
            return 0

        wizard_name = args[0]
        x = args[1]
        y = args[2]

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return 0

        # Evaluate position safety (distance from walls, enemy visibility, etc.)
        safety_score = 0

        # Distance from walls
        if 2 <= x <= 17 and 2 <= y <= 12:
            safety_score += 10

        # Distance from enemy
        for wizard in game_instance.wizards:
            if wizard.name != wizard_name["value"]:
                distance = abs(wizard.x - x) + abs(wizard.y - y)
                if distance > 6:
                    safety_score += 5
                elif distance < 3:
                    safety_score -= 10

        return safety_score

    return position_evaluator