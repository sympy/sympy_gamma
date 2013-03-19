import sympy
import collections
import stepprinter
from stepprinter import functionnames, Equals, Rule
from sympy.functions.elementary.trigonometric import TrigonometricFunction
from sympy.simplify import fraction
from sympy.strategies.core import switch, identity, do_one, null_safe, condition

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

evaluators = {}
def evaluates(rule):
    def _evaluates(func):
        func.rule = rule
        evaluators[rule] = func
        return func
    return _evaluates

# Method based on that on SIN, described in "Symbolic Integration: The
# Stormy Decade"

def find_substitutions(integrand, symbol, u_var):
    results = []

    def splice(l, index, item):
        return list(l[:index]) + [item] + list(l[index+1:])

    def test_subterm(replaced_integrand, u_diff):
        quotient = sympy.trigsimp(sympy.simplify(replaced_integrand / u_diff), deep=True)
        if quotient.is_constant(symbol):
            return quotient
        return None

    def possible_subterms(term):
        if term.func in (sympy.sin, sympy.cos, sympy.tan,
                         sympy.asin, sympy.acos, sympy.atan,
                         sympy.exp, sympy.log):
            return [(term.args[0], term.func(u_var))]
        elif term.func == sympy.Mul:
            r = []
            for i, u in enumerate(term.args):
                numer, denom = fraction(u)
                if numer == 1:
                    r.append((denom, sympy.Mul(*splice(term.args, i, 1/u_var))))
                else:
                    r.append((u, sympy.Mul(*splice(term.args, i, u_var))))
            for i, term in enumerate(term.args):
                for u, replaced in possible_subterms(term):
                    r.append((u, integrand.func(*splice(integrand.args, i, replaced))))
            return r
        elif term.func == sympy.Pow:
            if term.args[1].is_constant(symbol):
                return [(term.args[0], u_var ** term.args[1])]
            elif term.args[0].is_constant(symbol):
                return [(term.args[1], term.args[0] ** u_var)]
        return []

    for u, replaced in possible_subterms(integrand):
        new_integrand = test_subterm(replaced.rewrite('sincos'), u.rewrite('sincos').diff(symbol))
        if new_integrand is not None:
            constant = new_integrand.as_coeff_mul()[0]
            results.append((u, constant, new_integrand))

    return results

def rewriter(condition, rewrite):
    """Strategy that rewrites an integrand."""
    def _rewriter(integral):
        integrand, symbol = integral
        if condition(*integral):
            rewritten = rewrite(*integral)
            if rewritten != integrand:
                return RewriteRule(
                    rewritten,
                    integral_steps(rewritten, symbol),
                    integrand, symbol)
    return _rewriter

def alternatives(*rules):
    """Strategy that makes an AlternativeRule out of multiple possible results."""
    def _alternatives(integral):
        alts = []
        for rule in rules:
            result = rule(integral)
            if result and not isinstance(result, DontKnowRule) and result != integral:
                alts.append(result)
        if len(alts) == 1:
            return alts[0]
        elif len(alts) > 1:
            return AlternativeRule(alts, *integral)
    return _alternatives

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
    elif base.is_constant(symbol) and exp.func == sympy.Symbol:
        return ExpRule(base, exp, integrand, symbol)

def exp_rule(integral):
    integrand, symbol = integral
    if integrand.args[0].func == sympy.Symbol:
        return ExpRule(sympy.E, integrand.args[0], integrand, symbol)

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
    elif func == sympy.sec:
        rewritten = sympy.Mul(
            integrand,
            sympy.sec(*integrand.args) + sympy.tan(*integrand.args),
            1 / (sympy.sec(*integrand.args) + sympy.tan(*integrand.args)),
            evaluate=False)
    elif func == sympy.csc:
        rewritten = sympy.Mul(
            integrand,
            sympy.csc(*integrand.args) + sympy.cot(*integrand.args),
            1 / (sympy.csc(*integrand.args) + sympy.cot(*integrand.args)),
            evaluate=False)
    return RewriteRule(
        rewritten,
        integral_steps(rewritten, symbol, u_var=integral.u_var),
        integrand, symbol
    )

def substitution_rule(integral):
    integrand, symbol = integral

    u_var = integral.u_var
    substitutions = find_substitutions(integrand, symbol, u_var)
    if substitutions:
        ways = []
        new_u = integral.new_u_var(u_var)
        for u_func, c, substituted in substitutions:
            ways.append(URule(u_var, u_func, c,
                              integral_steps(substituted, u_var, u_var=new_u),
                              integrand, symbol))

        if len(ways) > 1:
            return AlternativeRule(ways, integrand, symbol)
        elif ways:
            return ways[0]

    elif integrand.has(sympy.exp):
        u_func = sympy.exp(symbol)
        c = 1
        substituted = integrand / u_func.diff(symbol)
        substituted = substituted.subs(u_func, u_var)
        new_u = integral.new_u_var(u_var)
        return URule(u_var, u_func, c,
                     integral_steps(substituted, u_var, u_var=new_u),
                     integrand, symbol)

partial_fractions_rule = rewriter(
    lambda integrand, symbol: integrand.is_rational_function(),
    lambda integrand, symbol: integrand.apart(symbol))

distribute_expand_rule = rewriter(
    lambda integrand, symbol: (
        all(arg.is_Pow or arg.is_polynomial(symbol) for arg in integrand.args)
        or integrand.func == sympy.Pow),
    lambda integrand, symbol: integrand.expand())

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
            sympy.exp: exp_rule,
            sympy.Add: add_rule,
            sympy.Mul: mul_rule,
            TrigonometricFunction: trig_rule,
            'constant': constant_rule
        })),
        null_safe(
            alternatives(
                substitution_rule,
                condition(lambda integral: key(integral) == sympy.Mul,
                          partial_fractions_rule),
                condition(lambda integral: key(integral) in (sympy.Mul, sympy.Pow),
                          distribute_expand_rule))),
        fallback_rule)(integral)

@evaluates(ConstantRule)
def eval_constant(constant, integrand, symbol):
    return constant * symbol

@evaluates(ConstantTimesRule)
def eval_constanttimes(constant, other, substep, integrand, symbol):
    return constant * integrate(substep)

@evaluates(PowerRule)
def eval_power(base, exp, integrand, symbol):
    return (base ** (exp + 1)) / (exp + 1)

@evaluates(ExpRule)
def eval_exp(base, exp, integrand, symbol):
    return integrand / sympy.ln(base)

@evaluates(AddRule)
def eval_add(substeps, integrand, symbol):
    return sum(map(integrate, substeps))

@evaluates(URule)
def eval_u(u_var, u_func, constant, substep, integrand, symbol):
    result = constant * integrate(substep)
    return result.subs(u_var, u_func)

@evaluates(TrigRule)
def eval_trig(func, arg, integrand, symbol):
    if func == sympy.sin:
        return -sympy.cos(arg)
    elif func == sympy.cos:
        return sympy.sin(arg)

@evaluates(LogRule)
def eval_log(func, integrand, symbol):
    return sympy.ln(sympy.Abs(func))

@evaluates(ArctanRule)
def eval_arctan(integrand, symbol):
    return sympy.atan(symbol)

@evaluates(AlternativeRule)
def eval_alternative(alternatives, integrand, symbol):
    return integrate(alternatives[0])

@evaluates(RewriteRule)
def eval_rewrite(rewritten, substep, integrand, symbol):
    return integrate(substep)

@evaluates(DontKnowRule)
def eval_dontknow(integrand, symbol):
    return sympy.integrate(integrand, symbol)

def integrate(rule):
    return evaluators[rule.__class__](*rule)

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
                           integrate(rule))))

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
                self.format_math(integrate(rule))))

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
                           integrate(rule))))

    def print_Add(self, rule):
        with self.new_step():
            self.append("Integrate term-by-term:")
            for substep in rule.substeps:
                with self.new_level():
                    self.print_rule(substep)
            self.append("The result is: {}".format(
                self.format_math(integrate(rule))))

    def print_U(self, rule):
        with self.new_step():
            u = rule.u_var
            du = sympy.Symbol('d' + u.name)
            # commutative always puts the symbol at the end when printed
            dx = sympy.Symbol('d' + rule.symbol.name, commutative=0)
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

            self.append(self.format_math_display(integrate(rule)))

    def print_Trig(self, rule):
        with self.new_step():
            if rule.func == sympy.sin:
                self.append("The integral of sine is negative cosine:")
            elif rule.func == sympy.cos:
                self.append("The integral of cosine is sine:")
            self.append(self.format_math_display(
                Equals(sympy.Integral(rule.context, rule.symbol),
                       integrate(rule))))

    def print_Exp(self, rule):
        with self.new_step():
            if rule.base == sympy.E:
                self.append("The integral of the exponential function is itself.")
            else:
                self.append("The integral of an exponential function is itself"
                            " divided by the natural logarithm of the base.")
            self.append(self.format_math_display(
                Equals(sympy.Integral(rule.context, rule.symbol),
                       integrate(rule))))

    def print_Log(self, rule):
        with self.new_step():
            self.append("The integral of {} is {}.".format(
                self.format_math(1 / rule.func),
                self.format_math(integrate(rule))
            ))

    def print_Arctan(self, rule):
        with self.new_step():
            self.append("The integral of {} is {}.".format(
                self.format_math(1 / (1 + rule.symbol ** 2)),
                self.format_math(integrate(rule))
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
        self.alternative_functions_printed = set()
        stepprinter.HTMLPrinter.__init__(self)
        IntegralPrinter.__init__(self, rule)

    def print_Alternative(self, rule):
        # TODO: make more robust
        if rule.context.func in self.alternative_functions_printed:
            self.print_rule(rule.alternatives[0])
        else:
            self.alternative_functions_printed.add(rule.context.func)
            with self.new_step():
                self.append("There are multiple ways to do this derivative.")
                for index, r in enumerate(rule.alternatives):
                    with self.new_collapsible():
                        self.append_header("Method #{}".format(index + 1))
                        with self.new_level():
                            self.print_rule(r)

    def finalize(self):
        answer = integrate(self.rule)
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
