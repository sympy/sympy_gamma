import sympy
import collections
import itertools

import stepprinter
from stepprinter import functionnames, Equals

from sympy.core.function import AppliedUndef
from sympy.functions.elementary.trigonometric import TrigonometricFunction

def concat(l):
    return list(itertools.chain.from_iterable(l))

def Rule(name, props=""):
    return collections.namedtuple(name, props + " context symbol")

NumberRule = Rule("NumberRule", "number")
ConstantTimesRule = Rule("ConstantTimesRule", "constant other substep")
PowerRule = Rule("PowerRule", "f")
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

def diffsteps(f, symbol):
    rule = type(f)

    if f.is_constant(symbol):
        return NumberRule(f, f, symbol)
    elif rule == sympy.Symbol:
        return PowerRule(f, f, symbol)
    elif rule == sympy.Pow:
        base, exp = f.as_base_exp()
        r = PowerRule(f, f, symbol)
        chain = base

        if base.is_constant(symbol):
            r = ExpRule(f, base, f, symbol)
            chain = exp

        if type(chain) != sympy.Symbol:
            return ChainRule(r, chain, diffsteps(chain, symbol), f, symbol)
        else:
            return r
    elif rule == sympy.Add:
        terms = f.args
        return AddRule([diffsteps(g, symbol) for g in terms], f, symbol)
    elif rule == sympy.Mul:
        terms = f.args
        is_div = 1 / sympy.Wild("denominator")
        if len(terms) == 2:
            if terms[0].is_constant(symbol):
                return ConstantTimesRule(terms[0], terms[1],
                                         diffsteps(terms[1], symbol), f, symbol)
            elif terms[1].is_constant(symbol):
                return ConstantTimesRule(terms[1], terms[0],
                                         diffsteps(terms[0], symbol), f, symbol)
            elif (terms[1].match(is_div) and
                type(terms[1]) == sympy.Pow and terms[1].args[1] == -1):
                numerator = terms[0]
                denominator = terms[1].args[0]
            elif (terms[0].match(is_div) and
                  type(terms[0]) == sympy.Pow and terms[0].args[1] == -1):
                numerator = terms[1]
                denominator = terms[0].args[0]
            else:
                return MulRule(terms, [diffsteps(g, symbol) for g in terms],
                               f, symbol)

            return DivRule(numerator, denominator,
                           diffsteps(numerator, symbol),
                           diffsteps(denominator, symbol), f, symbol)
        else:
            return MulRule(terms, [diffsteps(g, symbol) for g in terms], f, symbol)
    elif isinstance(f, TrigonometricFunction):
        if rule in (sympy.sin, sympy.cos):
            diffrule = TrigRule(f, f, symbol)
            arg = f.args[0]
            if type(arg) != sympy.Symbol:
                return ChainRule(diffrule, arg,
                                 diffsteps(arg, symbol), f, symbol)
            return diffrule
        elif rule == sympy.tan:
            f_r = sympy.sin(*f.args) / sympy.cos(*f.args)
            return RewriteRule(f_r, diffsteps(f_r, symbol), f, symbol)
        elif rule == sympy.cot:
            f_r_1 = 1 / sympy.tan(*f.args)
            f_r_2 = sympy.cos(*f.args) / sympy.sin(*f.args)
            return AlternativeRule([
                RewriteRule(f_r_1, diffsteps(f_r_1, symbol), f, symbol),
                RewriteRule(f_r_2, diffsteps(f_r_2, symbol), f, symbol)
            ], f, symbol)
        else:
            return DontKnowRule(f, symbol)
    elif rule == sympy.exp:
        exp = f.args[0]
        if type(exp) == sympy.Symbol:
            return ExpRule(f, sympy.E, f, symbol)
        return ChainRule(ExpRule(f, sympy.E, f, symbol),
                         exp, diffsteps(exp, symbol), f, symbol)
    elif rule == sympy.log:
        arg = f.args[0]
        if len(f.args) == 2:
            base = f.args[1]
        else:
            base = sympy.E
        if type(arg) == sympy.Symbol:
            return LogRule(arg, base, f, symbol)
        return ChainRule(LogRule(arg, base, f, symbol),
                         arg, diffsteps(arg, symbol), f, symbol)
    elif isinstance(f, AppliedUndef):
        return FunctionRule(f, symbol)
    else:
        return DontKnowRule(f, symbol)


def diffmanually(rule):
    if isinstance(rule, PowerRule):
        base, exp = rule.f.as_base_exp()
        return exp * (base ** (exp - 1))
    elif isinstance(rule, NumberRule):
        return 0
    elif isinstance(rule, ConstantTimesRule):
        return rule.constant * diffmanually(rule.substep)
    elif isinstance(rule, ChainRule):
        return diffmanually(rule.substep) * diffmanually(rule.innerstep)
    elif isinstance(rule, AddRule):
        return sum(map(diffmanually, rule.substeps))
    elif isinstance(rule, MulRule):
        result = []
        for index in range(len(rule.terms)):
            intermediate = []
            for i in range(len(rule.terms)):
                if i == index:
                    intermediate.append(diffmanually(rule.substeps[i]))
                else:
                    intermediate.append(rule.terms[i])
            result.append(reduce(lambda x,y: x*y, intermediate))
        return sum(result)
    elif isinstance(rule, DivRule):
        f, g = rule.numerator, rule.denominator
        fp, gp = diffmanually(rule.numerstep), diffmanually(rule.denomstep)
        return (g * fp - f * gp)/(g**2)
    elif isinstance(rule, TrigRule):
        if type(rule.f) == sympy.sin:
            return sympy.cos(*rule.f.args)
        elif type(rule.f) == sympy.cos:
            return -sympy.sin(*rule.f.args)
    elif isinstance(rule, ExpRule):
        if rule.base == sympy.E:
            return rule.f
        return rule.f * sympy.ln(rule.base)
    elif isinstance(rule, LogRule):
        if rule.base == sympy.E:
            return 1 / rule.arg
        return 1 / (rule.arg * sympy.ln(rule.base))
    elif isinstance(rule, AlternativeRule):
        return diffmanually(rule.alternatives[0])
    elif isinstance(rule, DontKnowRule):
        return rule.context.diff(rule.symbol)
    elif isinstance(rule, RewriteRule):
        return diffmanually(rule.substep)
    elif isinstance(rule, FunctionRule):
        return rule.context.diff(rule.symbol)

class DiffPrinter(object):
    def __init__(self, rule):
        self.print_rule(rule)
        self.rule = rule

    def print_rule(self, rule):
        if isinstance(rule, PowerRule):
            self.print_Power(rule)
        elif isinstance(rule, ChainRule):
            self.print_Chain(rule)
        elif isinstance(rule, NumberRule):
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
            base, exp = rule.f.as_base_exp()
            self.append("Apply the power rule: {0} goes to {1}".format(
                self.format_math(rule.f),
                self.format_math(diffmanually(rule))))

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
                self.format_math(diffmanually(rule))))

    def print_Add(self, rule):
        with self.new_step():
            self.append("Differentiate {} term by term:".format(
                self.format_math(rule.context)))
            with self.new_level():
                for substep in rule.substeps:
                    self.print_rule(substep)
            self.append("The result is: {}".format(
                self.format_math(diffmanually(rule))))

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

            self.append("The result is: " + self.format_math(diffmanually(rule)))

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
            self.append(self.format_math(diffmanually(rule)))

    def print_Chain(self, rule):
        self.print_rule(rule.substep)
        with self.new_step():
            if isinstance(rule.innerstep, FunctionRule):
                self.append(
                    "Then, apply the chain rule. Multiply by {}:".format(
                        self.format_math(
                            sympy.Derivative(rule.inner, rule.symbol))))
                self.append(self.format_math_display(diffmanually(rule)))
            else:
                self.append(
                    "Then, apply the chain rule. Multiply by {}:".format(
                        self.format_math(
                            sympy.Derivative(rule.inner, rule.symbol))))
                with self.new_level():
                    self.print_rule(rule.innerstep)
                    self.append("The result of the chain rule is:")
                    self.append(self.format_math_display(diffmanually(rule)))

    def print_Trig(self, rule):
        with self.new_step():
            if type(rule.f) == sympy.sin:
                self.append("The derivative of sine is cosine:")
            elif type(rule.f) == sympy.cos:
                self.append("The derivative of cosine is negative sine:")
            self.append("{}".format(
                self.format_math_display(Equals(
                    sympy.Derivative(rule.f, rule.symbol),
                    diffmanually(rule)))))

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
                                            diffmanually(rule)))))

    def print_Log(self, rule):
        with self.new_step():
            if rule.base == sympy.E:
                self.append("The derivative of {} is {}.".format(
                    self.format_math(rule.context),
                    self.format_math(diffmanually(rule))
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
                        diffmanually(rule)))))

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
                       diffmanually(rule))))

    def print_DontKnow(self, rule):
        with self.new_step():
            self.append("Don't know the steps in finding this derivative.")
            self.append("But the derivative is")
            self.append(self.format_math_display(diffmanually(rule)))

class HTMLPrinter(DiffPrinter, stepprinter.HTMLPrinter):
    def __init__(self, rule):
        stepprinter.HTMLPrinter.__init__(self)
        DiffPrinter.__init__(self, rule)

    def print_Alternative(self, rule):
        with self.new_step():
            self.append("There are multiple ways to do this derivative.")
            for index, r in enumerate(rule.alternatives):
                with self.new_collapsible():
                    self.append_header("Method #{}".format(index + 1))
                    with self.new_level():
                        self.print_rule(r)

    def finalize(self):
        answer = diffmanually(self.rule)
        # if answer:
        #     simp = sympy.simplify(answer)
        #     if simp != answer:
        #         with self.new_step():
        #             self.append("Now simplify:")
        #             self.append(self.format_math_display(simp))
        self.lines.append('</ol>')
        return '\n'.join(self.lines)

def print_html_steps(function, symbol):
    a = HTMLPrinter(diffsteps(function, symbol))
    return a.finalize()
