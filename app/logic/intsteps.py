from __future__ import absolute_import
import sympy
from . import stepprinter
from .stepprinter import replace_u_var

from sympy.integrals.manualintegrate import (
    _manualintegrate, integral_steps, evaluates,
    ConstantRule, ConstantTimesRule, PowerRule, AddRule, URule,
    PartsRule, CyclicPartsRule, TrigRule, ExpRule, ReciprocalRule, ArctanRule,
    AlternativeRule, DontKnowRule, RewriteRule
)

# Need this to break loops
# TODO: add manualintegrate flag to integrate
_evaluating = None
@evaluates(DontKnowRule)
def eval_dontknow(context, symbol):
    global _evaluating
    if _evaluating == context:
        return None
    _evaluating = context
    result = sympy.integrate(context, symbol)
    _evaluating = None
    return result


def contains_dont_know(rule):
    if isinstance(rule, DontKnowRule):
        return True
    else:
        for val in rule._asdict().values():
            if isinstance(val, tuple):
                if contains_dont_know(val):
                    return True
            elif isinstance(val, list):
                if any(contains_dont_know(i) for i in val):
                    return True
    return False

def filter_unknown_alternatives(rule):
    if isinstance(rule, AlternativeRule):
        alternatives = list([r for r in rule.alternatives if not contains_dont_know(r)])
        if not alternatives:
            alternatives = rule.alternatives
        return AlternativeRule(alternatives, rule.context, rule.symbol)
    return rule

class IntegralPrinter(object):
    def __init__(self, rule):
        self.rule = rule
        self.print_rule(rule)
        self.u_name = 'u'
        self.u = self.du = None

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
        elif isinstance(rule, PartsRule):
            self.print_Parts(rule)
        elif isinstance(rule, CyclicPartsRule):
            self.print_CyclicParts(rule)
        elif isinstance(rule, TrigRule):
            self.print_Trig(rule)
        elif isinstance(rule, ExpRule):
            self.print_Exp(rule)
        elif isinstance(rule, ReciprocalRule):
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
                    sympy.Eq(sympy.Integral(rule.constant, rule.symbol),
                           _manualintegrate(rule))))

    def print_ConstantTimes(self, rule):
        with self.new_step():
            self.append("The integral of a constant times a function "
                        "is the constant times the integral of the function:")
            self.append(self.format_math_display(
                sympy.Eq(
                    sympy.Integral(rule.context, rule.symbol),
                    rule.constant * sympy.Integral(rule.other, rule.symbol))))

            with self.new_level():
                self.print_rule(rule.substep)
            self.append("So, the result is: {}".format(
                self.format_math(_manualintegrate(rule))))

    def print_Power(self, rule):
        with self.new_step():
            self.append("The integral of {} is {} when {}:".format(
                self.format_math(rule.symbol ** sympy.Symbol('n')),
                self.format_math((rule.symbol ** (1 + sympy.Symbol('n'))) /
                                 (1 + sympy.Symbol('n'))),
                self.format_math(sympy.Ne(sympy.Symbol('n'), -1)),
            ))
            self.append(
                self.format_math_display(
                    sympy.Eq(sympy.Integral(rule.context, rule.symbol),
                           _manualintegrate(rule))))

    def print_Add(self, rule):
        with self.new_step():
            self.append("Integrate term-by-term:")
            for substep in rule.substeps:
                with self.new_level():
                    self.print_rule(substep)
            self.append("The result is: {}".format(
                self.format_math(_manualintegrate(rule))))

    def print_U(self, rule):
        with self.new_step(), self.new_u_vars() as (u, du):
            # commutative always puts the symbol at the end when printed
            dx = sympy.Symbol('d' + rule.symbol.name, commutative=0)
            self.append("Let {}.".format(
                self.format_math(sympy.Eq(u, rule.u_func))))
            self.append("Then let {} and substitute {}:".format(
                self.format_math(sympy.Eq(du, rule.u_func.diff(rule.symbol) * dx)),
                self.format_math(rule.constant * du)
            ))

            integrand = rule.constant * rule.substep.context.subs(rule.u_var, u)
            self.append(self.format_math_display(
                sympy.Integral(integrand, u)))

            with self.new_level():
                self.print_rule(replace_u_var(rule.substep, rule.symbol.name, u))

            self.append("Now substitute {} back in:".format(
                self.format_math(u)))

            self.append(self.format_math_display(_manualintegrate(rule)))

    def print_Parts(self, rule):
        with self.new_step():
            self.append("Use integration by parts:")

            u, v, du, dv = [sympy.Function(f)(rule.symbol) for f in 'u v du dv'.split()]
            self.append(self.format_math_display(
                r"""\int \operatorname{u} \operatorname{dv}
                = \operatorname{u}\operatorname{v} -
                \int \operatorname{v} \operatorname{du}"""
            ))

            self.append("Let {} and let {}.".format(
                self.format_math(sympy.Eq(u, rule.u)),
                self.format_math(sympy.Eq(dv, rule.dv))
            ))
            self.append("Then {}.".format(
                self.format_math(sympy.Eq(du, rule.u.diff(rule.symbol)))
            ))

            self.append("To find {}:".format(self.format_math(v)))

            with self.new_level():
                self.print_rule(rule.v_step)

            self.append("Now evaluate the sub-integral.")
            self.print_rule(rule.second_step)

    def print_CyclicParts(self, rule):
        with self.new_step():
            self.append("Use integration by parts, noting that the integrand"
                        " eventually repeats itself.")

            u, v, du, dv = [sympy.Function(f)(rule.symbol) for f in 'u v du dv'.split()]
            current_integrand = rule.context
            total_result = sympy.S.Zero
            with self.new_level():

                sign = 1
                for rl in rule.parts_rules:
                    with self.new_step():
                        self.append("For the integrand {}:".format(self.format_math(current_integrand)))
                        self.append("Let {} and let {}.".format(
                            self.format_math(sympy.Eq(u, rl.u)),
                            self.format_math(sympy.Eq(dv, rl.dv))
                        ))

                        v_f, du_f = _manualintegrate(rl.v_step), rl.u.diff(rule.symbol)

                        total_result += sign * rl.u * v_f
                        current_integrand = v_f * du_f

                        self.append("Then {}.".format(
                            self.format_math(
                                sympy.Eq(
                                    sympy.Integral(rule.context, rule.symbol),
                                    total_result - sign * sympy.Integral(current_integrand, rule.symbol)))
                        ))
                        sign *= -1
                with self.new_step():
                    self.append("Notice that the integrand has repeated itself, so "
                                "move it to one side:")
                    self.append("{}".format(
                        self.format_math_display(sympy.Eq(
                            (1 - rule.coefficient) * sympy.Integral(rule.context, rule.symbol),
                            total_result
                        ))
                    ))
                    self.append("Therefore,")
                    self.append("{}".format(
                        self.format_math_display(sympy.Eq(
                            sympy.Integral(rule.context, rule.symbol),
                            _manualintegrate(rule)
                        ))
                    ))


    def print_Trig(self, rule):
        with self.new_step():
            text = {
                'sin': "The integral of sine is negative cosine:",
                'cos': "The integral of cosine is sine:",
                'sec*tan': "The integral of secant times tangent is secant:",
                'csc*cot': "The integral of cosecant times cotangent is cosecant:",
            }.get(rule.func)

            if text:
                self.append(text)

            self.append(self.format_math_display(
                sympy.Eq(sympy.Integral(rule.context, rule.symbol),
                       _manualintegrate(rule))))

    def print_Exp(self, rule):
        with self.new_step():
            if rule.base == sympy.E:
                self.append("The integral of the exponential function is itself.")
            else:
                self.append("The integral of an exponential function is itself"
                            " divided by the natural logarithm of the base.")
            self.append(self.format_math_display(
                sympy.Eq(sympy.Integral(rule.context, rule.symbol),
                       _manualintegrate(rule))))

    def print_Log(self, rule):
        with self.new_step():
            self.append("The integral of {} is {}.".format(
                self.format_math(1 / rule.func),
                self.format_math(_manualintegrate(rule))
            ))

    def print_Arctan(self, rule):
        with self.new_step():
            self.append("The integral of {} is {}.".format(
                self.format_math(1 / (1 + rule.symbol ** 2)),
                self.format_math(_manualintegrate(rule))
            ))

    def print_Rewrite(self, rule):
        with self.new_step():
            self.append("Rewrite the integrand:")
            self.append(self.format_math_display(
                sympy.Eq(rule.context, rule.rewritten)))
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
        rule = filter_unknown_alternatives(rule)

        if len(rule.alternatives) == 1:
            self.print_rule(rule.alternatives[0])
            return

        if rule.context.func in self.alternative_functions_printed:
            self.print_rule(rule.alternatives[0])
        else:
            self.alternative_functions_printed.add(rule.context.func)
            with self.new_step():
                self.append("There are multiple ways to do this integral.")
                for index, r in enumerate(rule.alternatives):
                    with self.new_collapsible():
                        self.append_header("Method #{}".format(index + 1))
                        with self.new_level():
                            self.print_rule(r)

    def format_math_constant(self, math):
        return '<script type="math/tex; mode=display">{}</script>'.format(
            sympy.latex(math) + r'+ \mathrm{constant}')

    def finalize(self):
        rule = filter_unknown_alternatives(self.rule)
        answer = _manualintegrate(rule)
        if answer:
            simp = sympy.simplify(sympy.trigsimp(answer))
            if simp != answer:
                answer = simp
                with self.new_step():
                    self.append("Now simplify:")
                    self.append(self.format_math_display(simp))
            with self.new_step():
                self.append("Add the constant of integration:")
                self.append(self.format_math_constant(answer))
        self.lines.append('</ol>')
        self.lines.append('<hr/>')
        self.level = 0
        self.append('The answer is:')
        self.append(self.format_math_constant(answer))
        return '\n'.join(self.lines)

def print_html_steps(function, symbol):
    rule = integral_steps(function, symbol)
    if isinstance(rule, DontKnowRule):
        raise ValueError("Cannot evaluate integral")
    a = HTMLPrinter(rule)
    return a.finalize()
