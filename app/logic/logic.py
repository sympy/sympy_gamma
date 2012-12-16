import sys
from utils import Eval
from resultsets import find_result_set, fake_sympy_function, get_card
from sympy import latex, series, sympify, solve, Derivative, Integral, Symbol, diff, integrate
import sympy
import sympy.parsing.sympy_parser as sympy_parser

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
        except sympy_parser.TokenError:
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": "Invalid input"}
            ]
        except Exception as e:
            return self.handle_error(s, e)

        if result:
            evaluator, evaluated, variables = result

            if len(variables) > 0:
                var = variables.pop()
            else:
                var = None

            return self.prepare_cards(evaluator, evaluated, var)

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

        evaluated = sympify(s, convert_xor=True, locals={
            'integrate': sympy.Integral,
            'plot': lambda func: func,
            'diff': sympy.Derivative,
            'series': fake_sympy_function('series'),
            'solve': fake_sympy_function('solve'),
            'solve_poly_system': fake_sympy_function('solve_poly_system')
        })
        input_repr = repr(evaluated)
        namespace['input_evaluated'] = evaluated

        if isinstance(evaluated, sympy.Basic):
            variables = evaluated.atoms(Symbol)
        else:
            variables = []

        return evaluator, evaluated, variables

    def prepare_cards(self, evaluator, evaluated, var):
        input_repr = repr(evaluated)

        result = [
            {"title": "SymPy",
             "input": input_repr,
             "output": mathjax_latex(evaluated)},
        ]

        convert_input, cards = find_result_set(evaluated)
        input_evaluated, var = convert_input(evaluated, var)
        evaluator.set('input_evaluated', input_evaluated)

        # Come up with a solution to use all variables if more than 1
        # is entered.
        if var != None:  # See a better way to do this.
            input_repr = repr(input_evaluated)
            line = "simplify(input_evaluated)"
            simplified = evaluator.eval(line, use_none_for_exceptions=True)
            r = sympify(evaluator.eval(line, use_none_for_exceptions=True))

            if simplified != "None" and simplified != input_repr:
                result.append(
                    {"title": "Simplification", "input": simplified,
                     "output": mathjax_latex(r)})

            for card_name in cards:
                card = get_card(card_name)
                if not card:
                    continue

                try:
                    result.append({
                        'card': card_name,
                        'var': repr(var),
                        'title': card.format_title(input_repr),
                        'input': card.format_input(input_repr, var),
                        'pre_output': latex(
                            card.pre_output_function(input_repr, var)),
                        'parameters': card.card_info.get('parameters', [])
                    })
                except (SyntaxError, ValueError) as e:
                    pass
        return result
