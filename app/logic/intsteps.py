import sympy
import collections
import stepprinter
from stepprinter import functionnames, Equals
from sympy.functions.elementary.trigonometric import TrigonometricFunction
from sympy.strategies.core import switch, identity, do_one, null_safe

def Rule(name, props=""):
    # GOTCHA: namedtuple class name not considered!
    def __eq__(self, other):
        return self.__class__ == other.__class__ and tuple.__eq__(self, other)
    __neq__ = lambda self, other: not __eq__(self, other)
    cls = collections.namedtuple(name, props + " context symbol")
    cls.__eq__ = __eq__
    cls.__ne__ = __neq__
    return cls

ConstantRule = Rule("ConstantRule", "constant")
ConstantTimesRule = Rule("ConstantTimesRule", "constant other substep")
PowerRule = Rule("PowerRule", "base exp")
AddRule = Rule("AddRule", "substeps")
URule = Rule("URule", "u_var u_func constant substep")
TrigRule = Rule("TrigRule", "func arg")
ExpRule = Rule("ExpRule", "base exp")
LogRule = Rule("LogRule", "func")
ArctanRule = Rule("ArctanRule")
AlternativeRule = Rule("AlternativeRule", "alternatives")
DontKnowRule = Rule("DontKnowRule")
RewriteRule = Rule("RewriteRule", "rewritten substep")

class IntegralInfo(collections.namedtuple('IntegralInfo', 'integrand symbol')):
    def __new__(cls, *args, **kwargs):
        u_var = kwargs['u_var']
        del kwargs['u_var']
        self = super(IntegralInfo, cls).__new__(cls, *args, **kwargs)
        self.u_var = u_var
        return self

    @staticmethod
    def new_u_var(var):
        if len(var.name) == 3:
            num = int(var.name[2]) + 1
            name = var.name[0] + str(num)
        else:
            name = 'u_1'
        return sympy.Symbol(name)

def do(rule):
    def _do(integral):
        r = rule(integral)
        return evaluators[r.__class__](integral, *r)
    return _do

evaluators = {}
def evaluates(rule):
    def _evaluates(func):
        func.rule = rule
        evaluators[rule] = func
        return func
    return _evaluates

# Method based on that on SIN, described in "Symbolic Integration: The
# Stormy Decade"
def find_substitutions(integrand, symbol):
    results = []

    def subterm_constant(func, u_diff):
        quotient = sympy.simplify(integrand / (func * u_diff))
        if quotient.is_constant(symbol):
            return quotient
        return None

    def possible_subterms(term):
        if term.func in (sympy.sin, sympy.cos, sympy.tan,
                         sympy.asin, sympy.acos, sympy.atan,
                         sympy.exp, sympy.log):
            return [(term, arg) for arg in term.args]
        elif term.func == sympy.Mul:
            return [(arg, arg) for arg in term.args]
        elif term.func == sympy.Pow:
            if term.args[1].is_constant(symbol):
                return [(term, term.args[0])]
            elif term.args[0].is_constant(symbol):
                return [(term, term.args[1])]
        return []

    for func, term in possible_subterms(integrand):
        c = subterm_constant(func, term.diff(symbol))
        if c is not None:
            results.append((c, term))

        subterms = possible_subterms(term)
        for func, subterm in subterms:
            c = subterm_constant(func, subterm.diff(symbol))
            if c is not None:
                results.append((c, subterm))

    return results

def constant_rule(integral):
    integrand, symbol = integral
    return ConstantRule(integral.integrand, *integral)

def power_rule(integral):
    integrand, symbol = integral
    base, exp = integrand.as_base_exp()

    if exp.is_constant(symbol) and base.func == sympy.Symbol:
        if sympy.simplify(exp + 1) == 0:
            return LogRule(base, integrand, symbol)
        return PowerRule(base, exp, integrand, symbol)

def arctan_rule(integral):
    integrand, symbol = integral
    base, exp = integrand.as_base_exp()

    if sympy.simplify(exp + 1) == 0:
        a = sympy.Wild('a', exclude=[symbol])
        b = sympy.Wild('b', exclude=[symbol])
        match = base.match(a + b*symbol**2)
        if match:
            a, b = match[a], match[b]

            if a != 1 or b != 1:
                u_var = integral.u_var
                rewritten = sympy.Rational(1, a) * (base / a) ** (-1)
                u_func = sympy.sqrt(sympy.Rational(b, a)) * symbol
                constant = 1 / sympy.sqrt(sympy.Rational(b, a))
                substituted = rewritten.subs(u_func, u_var)

                if a == b:
                    substep = ArctanRule(integrand, symbol)
                else:
                    substep = URule(u_var, u_func, constant,
                                    ArctanRule(substituted, u_var),
                                    integrand, symbol)

                if a != 1:
                    other = (base / a) ** (-1)
                    return ConstantTimesRule(
                        sympy.Rational(1, a), other,
                        substep, integrand, symbol)
                return substep

            return ArctanRule(integrand, symbol)

def add_rule(integral):
    integrand, symbol = integral
    return AddRule(
        [integral_steps(g, symbol) for g in integrand.as_ordered_terms()],
        integrand, symbol)

def mul_rule(integral):
    integrand, symbol = integral
    args = integrand.args

    if len(args) == 2:
        if integrand.args[0].is_constant(symbol):
            return ConstantTimesRule(args[0], args[1],
                                     integral_steps(args[1], symbol),
                                     integrand, symbol)
        elif integrand.args[1].is_constant(symbol):
            return ConstantTimesRule(args[1], args[0],
                                     integral_steps(args[0], symbol),
                                     integrand, symbol)

    # TODO: integration by parts case

def trig_rule(integral):
    integrand, symbol = integral
    func = integrand.func
    if func in (sympy.sin, sympy.cos):
        arg = integrand.args[0]

        if type(arg) != sympy.Symbol:
            return DontKnowRule(integrand, symbol)

        return TrigRule(func, arg, integrand, symbol)

    if func == sympy.tan:
        rewritten = sympy.sin(*integrand.args) / sympy.cos(*integrand.args)
    elif func == sympy.cot:
        rewritten = sympy.cos(*integrand.args) / sympy.sin(*integrand.args)
    return RewriteRule(
        rewritten,
        integral_steps(rewritten, symbol, u_var=integral.u_var),
        integrand, symbol
    )

def substitution_rule(integral):
    integrand, symbol = integral

    substitutions = find_substitutions(integrand, symbol)
    if substitutions:
        ways = []
        u_var = integral.u_var
        new_u = integral.new_u_var(u_var)
        for substitution in substitutions:
            c, u_func = substitution
            substituted = integrand / u_func.diff(symbol) / c
            substituted = substituted.subs(u_func, u_var)
            ways.append(URule(u_var, u_func, c,
                              integral_steps(substituted, u_var, u_var=new_u),
                              integrand, symbol))

        if len(ways) > 1:
            return AlternativeRule(ways, integrand, symbol)
        elif ways:
            return ways[0]

    elif integrand.has(sympy.exp):
        u_var = integral.u_var
        u_func = sympy.exp(symbol)
        c = 1
        substituted = integrand / u_func.diff(symbol)
        substituted = substituted.subs(u_func, u_var)
        new_u = integral.new_u_var(u_var)
        return URule(u_var, u_func, c,
                     integral_steps(substituted, u_var, u_var=new_u),
                     integrand, symbol)

def partial_fractions_rule(integral):
    integrand, symbol = integral
    if integrand.is_rational_function():
        rewritten = sympy.apart(integrand)
        if rewritten != integrand:
            return RewriteRule(
                rewritten,
                integral_steps(rewritten, symbol),
                integrand, symbol)

def fallback_rule(integral):
    return DontKnowRule(*integral)

def integral_steps(integrand, symbol, **options):
    u_var = options.get('u_var', sympy.Symbol('u'))
    integral = IntegralInfo(integrand, symbol, u_var=u_var)

    def key(integral):
        integrand = integral.integrand
        if isinstance(integrand, TrigonometricFunction):
            return TrigonometricFunction
        elif integrand.is_constant(symbol):
            return 'constant'
        else:
            return integrand.func
    return do_one(
        null_safe(switch(key, {
            sympy.Pow: do_one(null_safe(power_rule), null_safe(arctan_rule)),
            sympy.Symbol: power_rule,
            sympy.Add: add_rule,
            sympy.Mul: mul_rule,
            TrigonometricFunction: trig_rule,
            'constant': constant_rule
        })),
        null_safe(substitution_rule),
        null_safe(partial_fractions_rule),
        fallback_rule)(integral)

def integral(rule):
    return evaluators[rule.__class__](*rule)

def intmanually(rule):
    if isinstance(rule, ConstantRule):
        return rule.constant * rule.symbol

    elif isinstance(rule, PowerRule):
        return (rule.base ** (rule.exp + 1)) / (rule.exp + 1)

    elif isinstance(rule, AddRule):
        return sum(map(intmanually, rule.substeps))

    elif isinstance(rule, ConstantTimesRule):
        return rule.constant * intmanually(rule.substep)

    elif isinstance(rule, URule):
        result = rule.constant * intmanually(rule.substep)
        return result.subs(rule.u_var, rule.u_func)

    elif isinstance(rule, TrigRule):
        if rule.func == sympy.sin:
            return -sympy.cos(rule.arg)
        elif rule.func == sympy.cos:
            return sympy.sin(rule.arg)

    elif isinstance(rule, LogRule):
        return sympy.ln(sympy.Abs(rule.func))

    elif isinstance(rule, ArctanRule):
        return sympy.atan(rule.symbol)

    elif isinstance(rule, RewriteRule):
        return intmanually(rule.substep)

    return None

class IntegralPrinter(object):
    def __init__(self, rule):
        self.rule = rule
        self.print_rule(rule)

    def print_rule(self, rule):
        if isinstance(rule, ConstantRule):
            self.print_Constant(rule)
        elif isinstance(rule, ConstantTimesRule):
            self.print_ConstantTimes(rule)
        elif isinstance(rule, PowerRule):
            self.print_Power(rule)
        elif isinstance(rule, AddRule):
            self.print_Add(rule)
        elif isinstance(rule, URule):
            self.print_U(rule)
        elif isinstance(rule, TrigRule):
            self.print_Trig(rule)
        elif isinstance(rule, ExpRule):
            self.print_Exp(rule)
        elif isinstance(rule, LogRule):
            self.print_Log(rule)
        elif isinstance(rule, ArctanRule):
            self.print_Arctan(rule)
        elif isinstance(rule, AlternativeRule):
            self.print_Alternative(rule)
        elif isinstance(rule, DontKnowRule):
            self.print_DontKnow(rule)
        elif isinstance(rule, RewriteRule):
            self.print_Rewrite(rule)
        else:
            self.append(repr(rule))

    def print_Constant(self, rule):
        with self.new_step():
            self.append("The integral of a constant is the constant "
                        "times the variable of integration:")
            self.append(
                self.format_math_display(
                    Equals(sympy.Integral(rule.constant, rule.symbol),
                           intmanually(rule))))

    def print_ConstantTimes(self, rule):
        with self.new_step():
            self.append("The integral of a constant times a function "
                        "is the constant times the integral of the function:")
            self.append(self.format_math_display(
                Equals(
                    sympy.Integral(rule.context, rule.symbol),
                    rule.constant * sympy.Integral(rule.other, rule.symbol))))

            with self.new_level():
                self.print_rule(rule.substep)
            self.append("So, the result is: {}".format(
                self.format_math(intmanually(rule))))

    def print_Power(self, rule):
        with self.new_step():
            self.append("The integral of {} is {}:".format(
                self.format_math(rule.symbol ** sympy.Symbol('n')),
                self.format_math((rule.symbol ** (1 + sympy.Symbol('n'))) /
                                 (1 + sympy.Symbol('n')))
            ))
            self.append(
                self.format_math_display(
                    Equals(sympy.Integral(rule.context, rule.symbol),
                           intmanually(rule))))

    def print_Add(self, rule):
        with self.new_step():
            self.append("Integrate term-by-term:")
            for substep in rule.substeps:
                with self.new_level():
                    self.print_rule(substep)
            self.append("The result is: {}".format(
                self.format_math(intmanually(rule))))

    def print_U(self, rule):
        with self.new_step():
            u = rule.u_var
            du = sympy.Symbol('d' + u.name)
            dx = sympy.Symbol('d' + rule.symbol.name)
            self.append("Let {}.".format(
                self.format_math(Equals(u, rule.u_func))))
            self.append("Then let {} and substitute {}.".format(
                self.format_math(Equals(du, rule.u_func.diff(rule.symbol) * dx)),
                self.format_math(rule.constant * du)
            ))

            with self.new_level():
                self.print_rule(rule.substep)

            self.append("Now substitute {} back in:".format(
                self.format_math(u)))

            self.append(self.format_math_display(intmanually(rule)))

    def print_Trig(self, rule):
        with self.new_step():
            if rule.func == sympy.sin:
                self.append("The integral of sine is negative cosine:")
            elif rule.func == sympy.cos:
                self.append("The integral of cosine is sine:")
            self.append(self.format_math_display(
                Equals(sympy.Integral(rule.context, rule.symbol),
                       intmanually(rule))))

    def print_Log(self, rule):
        with self.new_step():
            self.append("The integral of {} is {}.".format(
                self.format_math(1 / rule.func),
                self.format_math(intmanually(rule))
            ))

    def print_Arctan(self, rule):
        with self.new_step():
            self.append("The integral of {} is {}.".format(
                self.format_math(1 / (1 + rule.symbol ** 2)),
                self.format_math(intmanually(rule))
            ))

    def print_Rewrite(self, rule):
        with self.new_step():
            self.append("Rewrite the integrand:")
            self.append(self.format_math_display(
                Equals(rule.context, rule.rewritten)))
            self.print_rule(rule.substep)

    def print_DontKnow(self, rule):
        with self.new_step():
            self.append("Don't know the steps in finding this integral.")
            self.append("But the integral is")
            self.append(self.format_math_display(sympy.integrate(rule.context, rule.symbol)))


class HTMLPrinter(IntegralPrinter, stepprinter.HTMLPrinter):
    def __init__(self, rule):
        stepprinter.HTMLPrinter.__init__(self)
        IntegralPrinter.__init__(self, rule)

    def print_Alternative(self, rule):
        with self.new_step():
            self.append("There are multiple ways to do this derivative.")
            for index, r in enumerate(rule.alternatives):
                with self.new_collapsible():
                    self.append_header("Method #{}".format(index + 1))
                    with self.new_level():
                        self.print_rule(r)

    def finalize(self):
        answer = intmanually(self.rule)
        if answer:
            simp = sympy.simplify(sympy.trigsimp(answer))
            if simp != answer:
                answer = simp
                with self.new_step():
                    self.append("Now simplify:")
                    self.append(self.format_math_display(simp))
            with self.new_step():
                self.append("Add the constant of integration:")
                self.append(self.format_math_display(answer + sympy.Symbol('constant')))
        self.lines.append('</ol>')
        return '\n'.join(self.lines)

def print_html_steps(function, symbol):
    rule = integral_steps(function, symbol)
    a = HTMLPrinter(rule)
    return a.finalize()
