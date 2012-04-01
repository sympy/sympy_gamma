from utils import Eval
from sympy import latex, series, sympify, solve, Derivative, Integral, Symbol, diff, integrate

class SymPyGamma(object):

    def eval(self, s):
        r = self.try_sympy(s)
        if r:
            return r
        return [
                {"title": "Input", "input": s,
                    "output": "Can't handle the input."},
                ]

    def try_sympy(self, s):
        namespace = {}
        exec "from sympy.interactive import *" in {}, namespace
        a = Eval(namespace)
        # change to True to spare the user from exceptions:
        if not len(s):
            return
        r = a.eval(s, use_none_for_exceptions=False)
        if r is not None:
            result = [
                    {"title": "Input", "input": s},
                    {"title": "SymPy", "input": s, "output": r},
                    ]
            code = """\
s = %s
a = s.atoms(Symbol)
if len(a) == 1:
    x = a.pop()
    result = %s
else:
    result = None
result
"""
            var = a.eval(code % (s, 'x'), use_none_for_exceptions=True)
            # Come up with a solution to use all variables if more than 1
            # is entered.
            line = "simplify(%s)"
            simplified = a.eval(line % s, use_none_for_exceptions=True)
            r = sympify(a.eval(code % (s, line % s), use_none_for_exceptions=True))
            if simplified != "None" and simplified != s:
                result.append(
                        {"title": "Simplification", "input": simplified,
                            "output": latex(r)})
            if var != None: # See a better way to do this.
                var = var.replace("None", "").replace("\n", "")
                if len(var):
                    line = "solve(%s, {_var})".format(_var=var)
                    r = sympify(a.eval(code % (s, (line % s)), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                                {"title": "Roots", "input": line % simplified,
                                 "pre_output": latex(var), "output": latex(r)})

                    line = "diff(%s, {_var})".format(_var=var)
                    r = sympify(a.eval(code % (s, line % s), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                                {"title": "Derivative", "input": (line % simplified),
                                 "pre_output": latex(Derivative(s, Symbol(var))), 
                                 "output": latex(r)})

                    line = "integrate(%s, {_var})".format(_var=var)
                    r = sympify(a.eval(code % (s, line % s), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                                {"title": "Indefinite integral", "input": line % simplified,
                                 "pre_output": latex(Integral(s,Symbol(var))),
                                 "output": latex(r)})

                    line = "series(%s, {_var}, 0, 10)".format(_var=var)
                    r = sympify(a.eval(code % (s, line % s), use_none_for_exceptions=True))
                    if r and r != "None":
                        result.append(
                                {"title": "Series expansion around 0", "input": line % simplified,
                                 "output": latex(r)})
            return result
        else:
            return None
