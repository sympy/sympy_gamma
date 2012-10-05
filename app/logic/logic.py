import sys
from utils import Eval
from resultsets import find_result_set
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
    return ''.join(['<script type="math/tex; mode=display">', latex(obj),
                    '</script>'])


class SymPyGamma(object):

    def eval(self, s):
        r = self.try_sympy(s)
        if r:
            return r

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

    def try_sympy(self, s):
        namespace = {}
        exec PREEXEC in {}, namespace
        a = Eval(namespace)
        # change to True to spare the user from exceptions:
        if not len(s):
            return
        try:
            evaluated = sympify(s, convert_xor=True, locals={
                'integrate': sympy.Integral,
                'plot': lambda func: func
            })
            input_repr = repr(evaluated)
            namespace['input_evaluated'] = evaluated
        except sympy_parser.TokenError:
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": "Invalid input"}
            ]
        except Exception as e:
            return self.handle_error(s, e)

        if input_repr is not None:
            result = [
                {"title": "Input", "input": s},
                {"title": "SymPy", "input": s, "output": input_repr},
            ]

            if isinstance(evaluated, sympy.Basic):
                variables = evaluated.atoms(Symbol)
                if len(variables) == 1:
                    var = variables.pop()
                else:
                    var = None
            else:
                var = None

            convert_input, cards = find_result_set(evaluated)
            namespace['input_evaluated'], var = convert_input(evaluated, var)

            # Come up with a solution to use all variables if more than 1
            # is entered.
            if var != None:  # See a better way to do this.
                input_repr = repr(namespace['input_evaluated'])
                line = "simplify(input_evaluated)"
                simplified = a.eval(line, use_none_for_exceptions=True)
                r = sympify(a.eval(line, use_none_for_exceptions=True))

                if simplified != "None" and simplified != input_repr:
                    result.append(
                        {"title": "Simplification", "input": simplified,
                         "output": mathjax_latex(r)})

                for card in cards:
                    try:
                        r = card.eval(a, var)
                        if r != "None":
                            formatted_input = card.format_input(input_repr, var)
                            result.append(dict(
                                title=card.title,
                                input=formatted_input,
                                pre_output=latex(
                                    card.pre_output_function(input_repr, var)),
                                output=card.format_output(r, mathjax_latex)
                            ))
                    except SyntaxError:
                        pass
            return result
        else:
            return None
