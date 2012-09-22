import sys
from utils import Eval
from sympy import latex, series, sympify, solve, Derivative, Integral, Symbol, diff, integrate
import sympy
import sympy.parsing.sympy_parser as sympy_parser

PREEXEC = """from __future__ import division
from sympy import *
x, y, z = symbols('x,y,z')
k, m, n = symbols('k,m,n', integer=True)
f, g, h = map(Function, 'fgh')"""

class SymPyGamma(object):

    def eval(self, s):
        r = self.try_sympy(s)
        if r:
            return r
        return [
                {"title": "Input", "input": s,
                    "output": "Can't handle the input."},
                ]

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
            input_repr = repr(sympy_parser.parse_expr(s, convert_xor=True))
            namespace['input_evaluated'] = sympy_parser.parse_expr(s, convert_xor=True)
        except sympy_parser.TokenError:
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": "Invalid input"}
            ]
        except Exception as e:
            return self.handle_error(s, e)

        r = input_repr
        if r is not None:
            result = [
                {"title": "Input", "input": input_repr},
                {"title": "SymPy", "input": input_repr, "output": r,
                 "use_mathjax": False},
                    ]
            code = """\
a = input_evaluated.atoms(Symbol)
if len(a) == 1:
    x = a.pop()
    result = %s
else:
    result = None
result
"""
            var = a.eval(code % ('x'), use_none_for_exceptions=True)
            # Come up with a solution to use all variables if more than 1
            # is entered.
            line = "simplify(input_evaluated)"
            simplified = a.eval(line, use_none_for_exceptions=True)
            r = sympify(a.eval(code % (line), use_none_for_exceptions=True))
            s = 'input_evaluated'
            if simplified != "None" and simplified != input_repr:
                result.append(
                        {"title": "Simplification", "input": simplified,
                         "output": latex(r), "use_mathjax": True})
            if var != None: # See a better way to do this.
                var = var.replace("None", "").replace("\n", "")
                if len(var):
                    line = "solve(%s, {_var})".format(_var=var)
                    r = sympify(a.eval(code % (line % s), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                            {"title": "Roots", "input": line % simplified,
                             "pre_output": latex(var), "output": latex(r),
                             "use_mathjax": True})

                    line = "diff(%s, {_var})".format(_var=var)
                    r = sympify(a.eval(code % (line % s), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                                {"title": "Derivative", "input": (line % simplified),
                                 "pre_output": latex(Derivative(input_repr, Symbol(var))),
                                 "output": latex(r), "use_mathjax": True})

                    line = "integrate(%s, {_var})".format(_var=var)
                    r = sympify(a.eval(code % (line % s), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                                {"title": "Indefinite integral", "input": line % simplified,
                                 "pre_output": latex(Integral(input_repr,Symbol(var))),
                                 "output": latex(r), "use_mathjax": True})

                    line = "series(%s, {_var}, 0, 10)".format(_var=var)
                    r = sympify(a.eval(code % (line % s), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                                {"title": "Series expansion around 0", "input": line % simplified,
                                 "output": latex(r), "use_mathjax": True})
            return result
        else:
            return None
