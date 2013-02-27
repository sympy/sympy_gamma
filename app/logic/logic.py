import sys
import collections
from utils import Eval, latexify, topcall, removeSymPy, custom_implicit_transformation
from resultsets import find_result_set, fake_sympy_function, \
    get_card, FakeSymPyFunction
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
            parsed, evaluator, evaluated, variables = result

            if len(variables) > 0:
                var = variables.pop()
            else:
                var = None

            return self.prepare_cards(parsed, evaluator, evaluated, var)

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
        local_dict = {
            'integrate': sympy.Integral,
            'diff': sympy.Derivative,
            'plot': lambda func: func,
            'series': fake_sympy_function('series'),
            'solve': fake_sympy_function('solve'),
            'solve_poly_system': fake_sympy_function('solve_poly_system')
        }
        global_dict = {}
        exec 'from sympy import *' in global_dict
        parsed = stringify_expr(s, local_dict, global_dict, transformations)
        evaluated = eval_expr(parsed, local_dict, global_dict)
        input_repr = repr(evaluated)
        namespace['input_evaluated'] = evaluated

        if isinstance(evaluated, sympy.Basic):
            variables = evaluated.atoms(Symbol)
        else:
            variables = []

        return parsed, evaluator, evaluated, variables

    def prepare_cards(self, parsed, evaluator, evaluated, var):
        input_repr = repr(evaluated)
        first_func_name = topcall(parsed)

        if first_func_name:
            first_func = evaluator.get(first_func_name)
            is_function_not_class = (first_func and not isinstance(first_func, FunctionClass)
                                     and first_func_name and first_func_name[0].islower())
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

        convert_input, cards = find_result_set(evaluated)
        input_evaluated, var = convert_input(evaluated, var)
        evaluator.set('input_evaluated', input_evaluated)


        # Come up with a solution to use all variables if more than 1
        # is entered.
        if var is None:  # See a better way to do this.
            if is_function_not_class:
                result.append({
                    'title': 'Result',
                    'input': removeSymPy(parsed),
                    'output': mathjax_latex(evaluated)
                })
        else:
            input_repr = repr(input_evaluated)
            line = "simplify(input_evaluated)"
            simplified = evaluator.eval(line,
                                        use_none_for_exceptions=True,
                                        repr_expression=False)

            if (simplified != "None" and
                simplified != input_repr and
                not isinstance(input_evaluated, FakeSymPyFunction)):
                result.append(
                    {"title": "Simplification", "input": repr(simplified),
                     "output": mathjax_latex(simplified)})

            for card_name in cards:
                card = get_card(card_name)

                if not card:
                    continue

                try:
                    result.append({
                        'card': card_name,
                        'var': repr(var),
                        'title': card.format_title(input_evaluated),
                        'input': card.format_input(input_repr, var),
                        'pre_output': latex(
                            card.pre_output_function(input_repr, var)),
                        'parameters': card.card_info.get('parameters', [])
                    })
                except (SyntaxError, ValueError) as e:
                    pass
        return result
