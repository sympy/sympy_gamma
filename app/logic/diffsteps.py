import sympy
import collections
import itertools

import stepprinter
from stepprinter import functionnames, Equals

from sympy.core.function import AppliedUndef
from sympy.functions.elementary.trigonometric import TrigonometricFunction
from sympy.strategies.core import switch, identity

def concat(l):
    return list(itertools.chain.from_iterable(l))

def Rule(name, props=""):
    return collections.namedtuple(name, props + " context symbol")

ConstantRule = Rule("ConstantRule", "number")
ConstantTimesRule = Rule("ConstantTimesRule", "constant other substep")
PowerRule = Rule("PowerRule", "base exp")
AddRule = Rule("AddRule", "substeps")
MulRule = Rule("MulRule", "terms substeps")
DivRule = Rule("DivRule", "numerator denominator numerstep denomstep")
ChainRule = Rule("ChainRule", "substep inner innerstep")
TrigRule = Rule("TrigRule", "f")
ExpRule = Rule("ExpRule", "f base")
LogRule = Rule("LogRule", "arg base")
FunctionRule = Rule("FunctionRule")
AlternativeRule = Rule("AlternativeRule", "alternatives")
DontKnowRule = Rule("DontKnowRule")
RewriteRule = Rule("RewriteRule", "rewritten substep")

DerivativeInfo = collections.namedtuple('DerivativeInfo', 'expr symbol recurse')

def do(rule):
    def _do(derivative):
        r = rule(derivative)
        return evaluators[r.__class__](derivative, *r)
    return _do

evaluators = {}
def evaluates(rule):
    def _evaluates(func):
        func.rule = rule
        evaluators[rule] = func
        return func
    return _evaluates

def power_rule(derivative):
    expr, symbol = derivative.expr, derivative.symbol
    base, exp = expr.as_base_exp()

    if base.is_constant(symbol):
        r = ExpRule(expr, base, expr, symbol)
        chain = exp
    else:
        r = PowerRule(base, exp, expr, symbol)
        chain = base

    if chain.func != sympy.Symbol:
        return ChainRule(r, chain, diff_steps(chain, symbol), expr, symbol)
    else:
        return r

def add_rule(derivative):
    expr, symbol = derivative.expr, derivative.symbol
    return AddRule([derivative.recurse(arg, symbol) for arg in expr.args],
                   expr, symbol)

def constant_rule(derivative):
    expr, symbol = derivative.expr, derivative.symbol
    return ConstantRule(expr, expr, symbol)

def mul_rule(derivative):
    expr, symbol, recurse = derivative
    terms = expr.args
    is_div = 1 / sympy.Wild("denominator")
    if len(terms) == 2:
        if terms[0].is_constant(symbol):
            return ConstantTimesRule(terms[0], terms[1],
                                     recurse(terms[1], symbol), expr, symbol)
        elif terms[1].is_constant(symbol):
            return ConstantTimesRule(terms[1], terms[0],
                                     recurse(terms[0], symbol), expr, symbol)
        elif (terms[1].match(is_div) and
            type(terms[1]) == sympy.Pow and terms[1].args[1] == -1):
            numerator = terms[0]
            denominator = terms[1].args[0]
        elif (terms[0].match(is_div) and
              type(terms[0]) == sympy.Pow and terms[0].args[1] == -1):
            numerator = terms[1]
            denominator = terms[0].args[0]
        else:
            return MulRule(terms, [recurse(g, symbol) for g in terms],
                           expr, symbol)

        return DivRule(numerator, denominator,
                       recurse(numerator, symbol),
                       recurse(denominator, symbol), expr, symbol)
    else:
        return MulRule(terms, [recurse(g, symbol) for g in terms], expr, symbol)

def trig_rule(derivative):
    expr, symbol, recurse = derivative
    function = expr.func
    arg = expr.args[0]

    default = TrigRule(expr, expr, symbol)
    if type(arg) != sympy.Symbol:
        default = ChainRule(default, arg, recurse(arg, symbol),
                            expr, symbol)

    if function in (sympy.sin, sympy.cos):
        return default
    elif function == sympy.tan:
        f_r = sympy.sin(arg) / sympy.cos(arg)

        return AlternativeRule([
            default,
            RewriteRule(f_r, recurse(f_r, symbol), expr, symbol)
        ], expr, symbol)
    elif function == sympy.cot:
        f_r_1 = 1 / sympy.tan(arg)
        f_r_2 = sympy.cos(arg) / sympy.sin(arg)
        return AlternativeRule([
            default,
            RewriteRule(f_r_1, recurse(f_r_1, symbol), expr, symbol),
            RewriteRule(f_r_2, recurse(f_r_2, symbol), expr, symbol)
        ], expr, symbol)
    else:
        return DontKnowRule(f, symbol)

def exp_rule(derivative):
    expr, symbol, recurse = derivative
    exp = expr.args[0]
    if type(exp) == sympy.Symbol:
        return ExpRule(expr, sympy.E, expr, symbol)
    return ChainRule(ExpRule(expr, sympy.E, expr, symbol),
                     exp, recurse(exp, symbol), expr, symbol)

def log_rule(derivative):
    expr, symbol, recurse = derivative
    arg = expr.args[0]
    if len(expr.args) == 2:
        base = expr.args[1]
    else:
        base = sympy.E
        if type(arg) == sympy.Symbol:
            return LogRule(arg, base, expr, symbol)
        return ChainRule(LogRule(arg, base, expr, symbol),
                         arg, recurse(arg, symbol), expr, symbol)

def function_rule(derivative):
    return FunctionRule(derivative.expr, derivative.symbol)

@evaluates(ConstantRule)
def eval_constant(*args):
    return 0

@evaluates(ConstantTimesRule)
def eval_constanttimes(constant, other, substep, expr, symbol):
    return constant * diff(substep)

@evaluates(AddRule)
def eval_add(substeps, expr, symbol):
    results = [diff(step) for step in substeps]
    return sum(results)

@evaluates(DivRule)
def eval_div(numer, denom, numerstep, denomstep, expr, symbol):
    d_numer = diff(numerstep)
    d_denom = diff(denomstep)
    return (denom * d_numer - numer * d_denom) / (denom **2)

@evaluates(ChainRule)
def eval_chain(substep, inner, innerstep, expr, symbol):
    return diff(substep) * diff(innerstep)

@evaluates(PowerRule)
@evaluates(MulRule)
@evaluates(ExpRule)
@evaluates(LogRule)
@evaluates(DontKnowRule)
@evaluates(FunctionRule)
def eval_default(*args):
    func, symbol = args[-2], args[-1]

    if func.func == sympy.Symbol:
        func = sympy.Pow(func, 1, evaluate=False)

    # Automatically derive and apply the rule (don't use diff() directly as
    # chain rule is a separate step)
    substitutions = []
    mapping = {}
    constant_symbol = sympy.Symbol('a')
    for arg in func.args:
        if symbol in arg.free_symbols:
            mapping[symbol] = arg
            substitutions.append(symbol)
        else:
            mapping[constant_symbol] = arg
            substitutions.append(constant_symbol)

    rule = func.func(*substitutions).diff(symbol)
    return rule.subs(mapping)

@evaluates(TrigRule)
def eval_default_trig(*args):
    return sympy.trigsimp(eval_default(*args))

@evaluates(RewriteRule)
def eval_rewrite(rewritten, substep, expr, symbol):
    return diff(substep)

@evaluates(AlternativeRule)
def eval_alternative(alternatives, expr, symbol):
    return diff(alternatives[1])

def _make_diff(stepfunction):
    def _diff_steps(expr, symbol):
        deriv = DerivativeInfo(expr, symbol, _diff_steps)

        def key(deriv):
            expr = deriv.expr
            if isinstance(expr, TrigonometricFunction):
                return TrigonometricFunction
            elif isinstance(expr, AppliedUndef):
                return AppliedUndef
            elif expr.is_constant(symbol):
                return 'constant'
            else:
                return expr.func

        return switch(key, {
            sympy.Pow: stepfunction(power_rule),
            sympy.Symbol: stepfunction(power_rule),
            sympy.Add: stepfunction(add_rule),
            sympy.Mul: stepfunction(mul_rule),
            TrigonometricFunction: stepfunction(trig_rule),
            sympy.exp: stepfunction(exp_rule),
            sympy.log: stepfunction(log_rule),
            AppliedUndef: stepfunction(function_rule),
            'constant': stepfunction(constant_rule)
        })(deriv)
    return _diff_steps

diff_steps = _make_diff(identity)
diff = _make_diff(do)

def diff(rule):
    return evaluators[rule.__class__](*rule)

class DiffPrinter(object):
    def __init__(self, rule):
        self.print_rule(rule)
        self.rule = rule

    def print_rule(self, rule):
        if isinstance(rule, PowerRule):
            self.print_Power(rule)
        elif isinstance(rule, ChainRule):
            self.print_Chain(rule)
        elif isinstance(rule, ConstantRule):
            self.print_Number(rule)
        elif isinstance(rule, ConstantTimesRule):
            self.print_ConstantTimes(rule)
        elif isinstance(rule, AddRule):
            self.print_Add(rule)
        elif isinstance(rule, MulRule):
            self.print_Mul(rule)
        elif isinstance(rule, DivRule):
            self.print_Div(rule)
        elif isinstance(rule, TrigRule):
            self.print_Trig(rule)
        elif isinstance(rule, ExpRule):
            self.print_Exp(rule)
        elif isinstance(rule, LogRule):
            self.print_Log(rule)
        elif isinstance(rule, DontKnowRule):
            self.print_DontKnow(rule)
        elif isinstance(rule, AlternativeRule):
            self.print_Alternative(rule)
        elif isinstance(rule, RewriteRule):
            self.print_Rewrite(rule)
        elif isinstance(rule, FunctionRule):
            self.print_Function(rule)
        else:
            self.append(repr(rule))

    def print_Power(self, rule):
        with self.new_step():
            self.append("Apply the power rule: {0} goes to {1}".format(
                self.format_math(rule.context),
                self.format_math(diff(rule))))

    def print_Number(self, rule):
        with self.new_step():
            self.append("The derivative of the constant {} is zero.".format(
                self.format_math(rule.number)))

    def print_ConstantTimes(self, rule):
        with self.new_step():
            self.append("The derivative of a constant times a function "
                        "is the constant times the derivative of the function.")
            with self.new_level():
                self.print_rule(rule.substep)
            self.append("So, the result is: {}".format(
                self.format_math(diff(rule))))

    def print_Add(self, rule):
        with self.new_step():
            self.append("Differentiate {} term by term:".format(
                self.format_math(rule.context)))
            with self.new_level():
                for substep in rule.substeps:
                    self.print_rule(substep)
            self.append("The result is: {}".format(
                self.format_math(diff(rule))))

    def print_Mul(self, rule):
        with self.new_step():
            self.append("Apply the product rule:".format(
                self.format_math(rule.context)))

            fnames = map(lambda n: sympy.Function(n)(rule.symbol),
                         functionnames(len(rule.terms)))
            derivatives = map(lambda f: sympy.Derivative(f, rule.symbol), fnames)
            ruleform = []
            for index in range(len(rule.terms)):
                buf = []
                for i in range(len(rule.terms)):
                    if i == index:
                        buf.append(derivatives[i])
                    else:
                        buf.append(fnames[i])
                ruleform.append(reduce(lambda a,b: a*b, buf))
            self.append(self.format_math_display(
                Equals(sympy.Derivative(reduce(lambda a,b: a*b, fnames),
                                        rule.symbol),
                       sum(ruleform))))

            for fname, deriv, term, substep in zip(fnames, derivatives,
                                                   rule.terms, rule.substeps):
                self.append("{}; to find {}:".format(
                    self.format_math(Equals(fname, term)),
                    self.format_math(deriv)
                ))
                with self.new_level():
                    self.print_rule(substep)

            self.append("The result is: " + self.format_math(diff(rule)))

    def print_Div(self, rule):
        with self.new_step():
            f, g = rule.numerator, rule.denominator
            fp, gp = f.diff(rule.symbol), g.diff(rule.symbol)
            x = rule.symbol
            ff = sympy.Function("f")(x)
            gg = sympy.Function("g")(x)
            qrule_left = sympy.Derivative(ff / gg, rule.symbol)
            qrule_right = sympy.ratsimp(sympy.diff(sympy.Function("f")(x) /
                                                   sympy.Function("g")(x)))
            qrule = Equals(qrule_left, qrule_right)
            self.append("Apply the quotient rule, which is:")
            self.append(self.format_math_display(qrule))
            self.append("{} and {}.".format(self.format_math(Equals(ff, f)),
                                            self.format_math(Equals(gg, g))))
            self.append("To find {}:".format(self.format_math(ff.diff(rule.symbol))))
            with self.new_level():
                self.print_rule(rule.numerstep)
            self.append("To find {}:".format(self.format_math(gg.diff(rule.symbol))))
            with self.new_level():
                self.print_rule(rule.denomstep)
            self.append("Now plug in to the quotient rule:")
            self.append(self.format_math(diff(rule)))

    def print_Chain(self, rule):
        self.print_rule(rule.substep)
        with self.new_step():
            if isinstance(rule.innerstep, FunctionRule):
                self.append(
                    "Then, apply the chain rule. Multiply by {}:".format(
                        self.format_math(
                            sympy.Derivative(rule.inner, rule.symbol))))
                self.append(self.format_math_display(diff(rule)))
            else:
                self.append(
                    "Then, apply the chain rule. Multiply by {}:".format(
                        self.format_math(
                            sympy.Derivative(rule.inner, rule.symbol))))
                with self.new_level():
                    self.print_rule(rule.innerstep)
                self.append("The result of the chain rule is:")
                self.append(self.format_math_display(diff(rule)))

    def print_Trig(self, rule):
        with self.new_step():
            if type(rule.f) == sympy.sin:
                self.append("The derivative of sine is cosine:")
            elif type(rule.f) == sympy.cos:
                self.append("The derivative of cosine is negative sine:")
            self.append("{}".format(
                self.format_math_display(Equals(
                    sympy.Derivative(rule.f, rule.symbol),
                    diff(rule)))))

    def print_Exp(self, rule):
        with self.new_step():
            if rule.base == sympy.E:
                self.append("The derivative of {} is itself.".format(
                    self.format_math(sympy.exp(rule.symbol))))
            else:
                self.append("The derivative of {} is {}.".format(
                    self.format_math(rule.base ** rule.symbol),
                    self.format_math(rule.base ** rule.symbol * sympy.ln(rule.base))))
                self.append("So {}".format(
                    self.format_math(Equals(sympy.Derivative(rule.f, rule.symbol),
                                            diff(rule)))))

    def print_Log(self, rule):
        with self.new_step():
            if rule.base == sympy.E:
                self.append("The derivative of {} is {}.".format(
                    self.format_math(rule.context),
                    self.format_math(diff(rule))
                ))
            else:
                # This case shouldn't come up often, seeing as SymPy
                # automatically applies the change-of-base identity
                self.append("The derivative of {} is {}.".format(
                    self.format_math(sympy.log(rule.symbol, rule.base,
                                               evaluate=False)),
                    self.format_math(1/(rule.arg * sympy.ln(rule.base)))))
                self.append("So {}".format(
                    self.format_math(Equals(
                        sympy.Derivative(rule.context, rule.symbol),
                        diff(rule)))))

    def print_Alternative(self, rule):
        with self.new_step():
            self.append("There are multiple ways to do this derivative.")
            self.append("One way:")
            with self.new_level():
                self.print_rule(rule.alternatives[0])

    def print_Rewrite(self, rule):
        with self.new_step():
            self.append("Rewrite the function to be differentiated:")
            self.append(self.format_math_display(
                Equals(rule.context, rule.rewritten)))
            self.print_rule(rule.substep)

    def print_Function(self, rule):
        with self.new_step():
            self.append("Trivial:")
            self.append(self.format_math_display(
                Equals(sympy.Derivative(rule.context, rule.symbol),
                       diff(rule))))

    def print_DontKnow(self, rule):
        with self.new_step():
            self.append("Don't know the steps in finding this derivative.")
            self.append("But the derivative is")
            self.append(self.format_math_display(diff(rule)))

class HTMLPrinter(DiffPrinter, stepprinter.HTMLPrinter):
    def __init__(self, rule):
        self.alternative_functions_printed = set()
        stepprinter.HTMLPrinter.__init__(self)
        DiffPrinter.__init__(self, rule)

    def print_Alternative(self, rule):
        if rule.context.func in self.alternative_functions_printed:
            self.print_rule(rule.alternatives[0])
        elif len(rule.alternatives) == 2:
            self.print_rule(rule.alternatives[1])
        else:
            self.alternative_functions_printed.add(rule.context.func)
            with self.new_step():
                self.append("There are multiple ways to do this derivative.")
                for index, r in enumerate(rule.alternatives[1:]):
                    with self.new_collapsible():
                        self.append_header("Method #{}".format(index + 1))
                        with self.new_level():
                            self.print_rule(r)

    def finalize(self):
        answer = diff(self.rule)
        if answer:
            simp = sympy.simplify(answer)
            if simp != answer:
                with self.new_step():
                    self.append("Now simplify:")
                    self.append(self.format_math_display(simp))
        self.lines.append('</ol>')
        return '\n'.join(self.lines)

def print_html_steps(function, symbol):
    a = HTMLPrinter(diff_steps(function, symbol))
    return a.finalize()
