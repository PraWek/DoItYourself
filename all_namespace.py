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
        if not args or not isinstance(args, tuple):
            return "Invalid arguments"
        wizard_name = args[0]
        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"
        move_args = args[1]
        if not isinstance(move_args, tuple) or len(move_args) != 2:
            return "Invalid movement arguments"
        dx, dy = move_args

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
        if not args or not isinstance(args, tuple):
            return "Invalid arguments"
        wizard_name = args[0]
        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"
        spell_data = args[1]
        if not isinstance(spell_data, tuple) or len(spell_data) != 3:
            return "Invalid spell data"
        spell_name, target_x, target_y = spell_data
        if not isinstance(spell_name, dict) or spell_name.get("type") != "string":
            return "Invalid spell name"
        return game_instance.cast_spell(wizard_name["value"], spell_name["value"], target_x, target_y)

    return spell_handler


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
    }]