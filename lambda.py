from evaluate import evaluate

def lisp_lambda(params, body, env):
    def lambda_func(*args):
        param_names = flatten_params(params)
        new_env = env.copy()
        new_env.append(dict(zip(param_names, args)))
        return evaluate(body, new_env)

    return lambda_func


def flatten_params(params):
    """
    Преобразует вложенные параметры в плоский список.
    (a, (b, ())) -> [a, b]
    """
    result = []
    while params:
        if isinstance(params, tuple):
            result.append(params[0])
            params = params[1]
        else:
            break
    return result

# from calculation_functions import multiply
#
# names = [{
#     "*": {"function": multiply},
#     "x": 10,
#     "y": 20,
# }]
#
# params = ('a', ('b', ()))
# body = ('*', ('a', ('b', ())))
# my_lambda = lisp_lambda(params, body, names)
#
# result = my_lambda(3, 5)
# print(result)  # -> 15