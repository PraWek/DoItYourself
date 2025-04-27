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
        if not args or not isinstance(args, tuple) or len(args) != 3:
            return "Invalid arguments"

        wizard_name = args[0]
        dx = args[1]
        dy = args[2]

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
        if not args or not isinstance(args, tuple) or len(args) != 4:
            return "Invalid arguments"

        wizard_name = args[0]
        spell_name = args[1]
        target_x = args[2]
        target_y = args[3]

        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"
        if not isinstance(spell_name, dict) or spell_name.get("type") != "string":
            return "Invalid spell name"

        return game_instance.cast_spell(wizard_name["value"], spell_name["value"], target_x, target_y)

    return spell_handler


def create_move_wizard(game_instance):
    def move_handler(args):
        if not args or not isinstance(args, tuple) or len(args) != 2:
            return "Invalid arguments"

        wizard_name = args[0]
        if not isinstance(wizard_name, dict) or wizard_name.get("type") != "string":
            return "Invalid wizard name"

        direction = args[1]
        if not isinstance(direction, tuple) or len(direction) != 2:
            return "Invalid direction"

        dx = direction[0]
        dy = direction[1] if isinstance(direction[1], tuple) else ()
        if dy:
            dy = dy[0]
        else:
            dy = 0

        return game_instance.move_wizard(wizard_name["value"], dx, dy)

    return move_handler


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
        if not args or not isinstance(args, tuple):
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
    }]