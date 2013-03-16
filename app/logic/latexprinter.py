import sympy
from sympy.printing.latex import LatexPrinter

class GammaLatexPrinter(LatexPrinter):
    def _needs_function_brackets(self, expr):
        if expr.func == sympy.Abs:
            return False
        if not self._needs_brackets(expr):
            return True
        return super(GammaLatexPrinter, self)._needs_function_brackets(expr)


def latex(expr, **settings):
    settings['fold_func_brackets'] = True
    settings['inv_trig_style'] = 'power'
    return GammaLatexPrinter(settings).doprint(expr)
