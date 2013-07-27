import sys
import collections
from utils import Eval, latexify, topcall, arguments, removeSymPy, \
    custom_implicit_transformation
from resultsets import find_result_set, get_card, format_by_type
from sympy import latex, series, sympify, solve, Derivative, \
    Integral, Symbol, diff, integrate
import sympy
from sympy.core.function import FunctionClass
from sympy.parsing.sympy_parser import stringify_expr, eval_expr, \
    standard_transformations, convert_xor, TokenError

PREEXEC = """from __future__ import division
from sympy import *
import sympy
x, y, z = symbols('x,y,z')
k, m, n = symbols('k,m,n', integer=True)
f, g, h = map(Function, 'fgh')"""


def mathjax_latex(obj):
    if hasattr(obj, 'as_latex'):
        tex_code = obj.as_latex()
    else:
        tex_code = latex(obj)
    return ''.join(['<script type="math/tex; mode=display">', tex_code,
                    '</script>'])


class SymPyGamma(object):

    def eval(self, s):
        result = None

        try:
            result = self.eval_input(s)
        except TokenError:
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": "Invalid input"}
            ]
        except Exception as e:
            return self.handle_error(s, e)

        if result:
            parsed, arguments, evaluator, evaluated = result

            return self.prepare_cards(parsed, arguments, evaluator, evaluated)

    def handle_error(self, s, e):
        if isinstance(e, SyntaxError):
            error = {
                "input_start": e.text[:e.offset],
                "input_end": e.text[e.offset:],
                "msg": e.msg,
                "offset": e.offset
            }
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "exception_info": error}
            ]
        else:
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": str(e)}
            ]

    def eval_input(self, s):
        namespace = {}
        exec PREEXEC in {}, namespace
        evaluator = Eval(namespace)
        # change to True to spare the user from exceptions:
        if not len(s):
            return None

        transformations = standard_transformations + (convert_xor, custom_implicit_transformation)
        local_dict = {}
        global_dict = {}
        exec 'from sympy import *' in global_dict
        parsed = stringify_expr(s, local_dict, global_dict, transformations)
        evaluated = eval_expr(parsed, local_dict, global_dict)
        input_repr = repr(evaluated)
        namespace['input_evaluated'] = evaluated

        return parsed, arguments(parsed, evaluator), evaluator, evaluated

    def prepare_cards(self, parsed, arguments, evaluator, evaluated):
        input_repr = repr(evaluated)
        first_func_name = arguments[0]

        if first_func_name:
            first_func = evaluator.get(first_func_name)
            is_function_not_class = (
                first_func and
                not isinstance(first_func, FunctionClass) and
                not isinstance(first_func, sympy.Atom) and
                first_func_name and first_func_name[0].islower())
        else:
            first_func_name = first_func = None
            is_function_not_class = False

        if is_function_not_class:
            latex_input = ''.join(['<script type="math/tex; mode=display">',
                                   latexify(parsed, evaluator),
                                   '</script>'])
        else:
            latex_input = mathjax_latex(evaluated)

        result = [
            {"title": "SymPy",
             "input": removeSymPy(parsed),
             "output": latex_input},
        ]

        convert_input, cards, handles_function = find_result_set(arguments[0], evaluated)
        components = convert_input(arguments, evaluated)

        if 'input_evaluated' in components:
            evaluated = components['input_evaluated']

        evaluator.set('input_evaluated', evaluated)

        # Come up with a solution to use all variables if more than 1
        # is entered.
        if not cards and not components['variable'] and is_function_not_class:  # See a better way to do this.
            result.append({
                'title': 'Result',
                'input': removeSymPy(parsed),
                'output': format_by_type(evaluated, mathjax_latex)
            })
        else:
            input_repr = repr(evaluated)
            var = components['variable']

            # If the expression is something like 'lcm(2x, 3x)', display the
            # result of the function before the rest of the cards
            if is_function_not_class and not handles_function:
                result.append(
                    {"title": "Result", "input": "",
                     "output": mathjax_latex(evaluated)})

            line = "simplify(input_evaluated)"
            simplified = evaluator.eval(line,
                                        use_none_for_exceptions=True,
                                        repr_expression=False)
            if (simplified != "None" and
                simplified != evaluated):
                result.append(
                    {"title": "Simplification", "input": repr(simplified),
                     "output": mathjax_latex(simplified)})
            elif first_func_name == 'simplify':
                result.append(
                    {"title": "Simplification", "input": "",
                     "output": mathjax_latex(evaluated)})

            for card_name in cards:
                card = get_card(card_name)

                if not card:
                    continue

                try:
                    result.append({
                        'card': card_name,
                        'var': repr(var),
                        'title': card.format_title(evaluated),
                        'input': card.format_input(input_repr, components),
                        'pre_output': latex(
                            card.pre_output_function(evaluated, var)),
                        'parameters': card.card_info.get('parameters', [])
                    })
                except (SyntaxError, ValueError) as e:
                    pass
        return result

    def eval_card(self, card_name, expression, variable, parameters):
        card = get_card(card_name)

        if not card:
            raise KeyError

        _, arguments, evaluator, evaluated = self.eval_input(expression)

        convert_input, _, _ = find_result_set(arguments[0], evaluated)
        var = sympy.sympify(variable.encode('utf-8'))
        components = convert_input(arguments, evaluated)

        if 'input_evaluated' in components:
            evaluated = components['input_evaluated']

        evaluator.set('input_evaluated', evaluated)

        result = card.eval(evaluator, components, parameters)

        return {
            'value': repr(result),
            'output': card.format_output(result, mathjax_latex)
        }
