from calculation_functions import add, subtract, multiply, divide
from comparison_functions import less_than, greater_than, less_or_equal, greater_or_equal, equal
from evaluate import evaluate


def try_function(args):
    names = namespace()

    if not args or len(args) < 2:
        raise ValueError("try requires at least two arguments: expression and handler")

    expr, handler = args[0], args[1]
    try:
        return evaluate(expr, names)
    except Exception as e:
        return evaluate((handler, (str(e), ())), names)


def create_move_wizard(game_instance):
    def move_wizard(args):
        # Extract arguments from nested tuple structure
        def flatten_args(arg_tuple):
            result = []
            current = arg_tuple
            while isinstance(current, tuple) and len(current) == 2:
                result.append(current[0])
                current = current[1]
            if current != ():
                result.append(current)
            return result

        if not args:
            return "No arguments provided"

        flat_args = flatten_args(args)

        if len(flat_args) < 3:
            return "Not enough arguments"

        wizard_name = flat_args[0]
        dx = flat_args[1]
        dy = flat_args[2]

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"

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
        # Extract arguments from nested tuple structure
        def flatten_args(arg_tuple):
            result = []
            current = arg_tuple
            while isinstance(current, tuple) and len(current) == 2:
                result.append(current[0])
                current = current[1]
            if current != ():
                result.append(current)
            return result

        if not args:
            return "No arguments provided"

        flat_args = flatten_args(args)

        if len(flat_args) < 4:
            return "Not enough arguments"

        wizard_name = flat_args[0]
        spell_name = flat_args[1]
        target_x = flat_args[2]
        target_y = flat_args[3]

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"
        if not isinstance(spell_name, dict) or spell_name.get("type") != "string":
            return "Invalid spell name"

        return game_instance.cast_spell(wizard_name["value"], spell_name["value"], target_x, target_y)

    return spell_handler


def create_select_spell(game_instance):
    def spell_handler(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
            return "Invalid arguments"

        wizard_name = args[0]
        spell_name = args[1]

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"
        if not isinstance(spell_name, dict) or spell_name.get("type") != "string":
            return "Invalid spell name"

        return game_instance.select_spell(wizard_name["value"], spell_name["value"])

    return spell_handler


def create_toggle_ai(game_instance):
    def toggle_handler(_):
        return game_instance.toggle_ai()

    return toggle_handler


def create_get_wizard_health(game_instance):
    def get_health(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
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


def namespace():
    return [{
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
        "if": {"function": lambda args: args[1] if args and args[0] else (args[2] if len(args) > 2 else None)},
        "list": {"function": lambda args: list(args) if args else []},
        "car": {"function": lambda args: args[0][0] if args and args[0] else None},
        "cdr": {"function": lambda args: args[0][1:] if args and args[0] else []},
        "cons": {"function": lambda args: [args[0]] + list(args[1]) if len(args) >= 2 else args},
        "length": {"function": lambda args: len(args[0]) if args and hasattr(args[0], '__len__') else 0},
        "map": {"function": lambda args: [args[0](x) for x in args[1]] if len(args) >= 2 else []},
        "filter": {"function": lambda args: [x for x in args[1] if args[0](x)] if len(args) >= 2 else []},
        "reduce": {"function": lambda args: reduce_func(args[0], args[1], args[2] if len(args) > 2 else None) if len(
            args) >= 2 else None},
    }]


def reduce_func(func, iterable, initializer=None):
    import functools
    if initializer is not None:
        return functools.reduce(func, iterable, initializer)
    else:
        return functools.reduce(func, iterable)


def create_conditional_move(game_instance):
    def conditional_move(args):
        if not args or len(args) < 3:
            return False

        condition, true_action, false_action = args[0], args[1], args[2]

        # Evaluate condition
        try:
            result = evaluate(condition, namespace())
            action = true_action if result else false_action
            return evaluate(action, namespace())
        except:
            return False

    return conditional_move


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
