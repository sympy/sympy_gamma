import sympy
import collections
import itertools

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
AlternativeRule = Rule("AlternativeRule", "alternatives")
DontKnowRule = Rule("DontKnowRule")

def diffsteps(f, symbol=sympy.Symbol("x")):
    rule = type(f)
    if rule == sympy.Symbol:
        return PowerRule(f, f, symbol)
    elif isinstance(f, sympy.Number):
        return NumberRule(f, f, symbol)
    elif rule == sympy.Pow:
        base, exp = f.as_base_exp()
        if type(base) != sympy.Symbol:
            return ChainRule(PowerRule(f, f, symbol), base, diffsteps(base, symbol), f, symbol)
        return PowerRule(f, f, symbol)
    elif rule == sympy.Add:
        terms = f.args
        return AddRule([diffsteps(g, symbol) for g in terms], f, symbol)
    elif rule == sympy.Mul:
        terms = f.args
        is_div = 1 / sympy.Wild("denominator")
        if len(terms) == 2:
            if isinstance(terms[0], sympy.Number):
                return ConstantTimesRule(terms[0], terms[1], diffsteps(terms[1], symbol), f, symbol)
            elif (terms[1].match(is_div) and
                type(terms[1]) == sympy.Pow and terms[1].args[1] == -1):
                numerator = terms[0]
                denominator = terms[1].args[0]
            elif (terms[0].match(is_div) and
                  type(terms[0]) == sympy.Pow and terms[0].args[1] == -1):
                numerator = terms[1]
                denominator = terms[0].args[0]
            else:
                return MulRule(terms, [diffsteps(g, symbol) for g in terms], f, symbol)

            return DivRule(numerator, denominator,
                           diffsteps(numerator, symbol),
                           diffsteps(denominator, symbol), f, symbol)
        else:
            return MulRule(terms, [diffsteps(g, symbol) for g in terms], f, symbol)
    elif isinstance(f, TrigonometricFunction):
        if rule in (sympy.sin, sympy.cos):
            if type(f.args[0]) != sympy.Symbol:
                return ChainRule(TrigRule(f, f, symbol), f.args[0], diffsteps(f.args[0], symbol), f, symbol)
            return TrigRule(f, f, symbol)
        elif rule == sympy.tan:
            return diffsteps(sympy.sin(*f.args) / sympy.cos(*f.args), symbol)
        elif rule == sympy.cot:
            return AlternativeRule([
                diffsteps(1 / sympy.tan(*f.args), symbol),
                diffsteps(sympy.cos(*f.args) / sympy.sin(*f.args), symbol)
            ], f, symbol)
        else:
            return DontKnowRule(f, symbol)
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
    elif isinstance(rule, AlternativeRule):
        return diffmanually(rule.alternatives[0])
    elif isinstance(rule, DontKnowRule):
        return rule.context.diff(rule.symbol)

def functionnames(numterms):
    if numterms == 2:
        return ["f", "g"]
    elif numterms == 3:
        return ["f", "g", "h"]
    else:
        return ["f_{}".format(i) for i in range(numterms)]

class Equals(sympy.Basic):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _latex(self, printer):
        return '{} = {}'.format(sympy.latex(self.left),
                                sympy.latex(self.right))

    def __str__(self):
        return '{} = {}'.format(str(self.left), str(self.right))

from contextlib import contextmanager
class DiffPrinter(object):
    def __init__(self, rule):
        self.lines = []
        self.level = 0
        self.print_rule(rule)
        self.rule = rule

    def format_math(self, math):
        return str(math)

    def format_math_display(self, math):
        return self.format_math(math)

    @contextmanager
    def new_level(self):
        self.level += 1
        yield self.level
        self.level -= 1

    @contextmanager
    def new_step(self):
        yield self.level
        self.lines.append('\n')

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
        elif isinstance(rule, DontKnowRule):
            self.print_DontKnow(rule)
        elif isinstance(rule, AlternativeRule):
            self.print_Alternative(rule)
        else:
            self.lines.append(repr(rule))

    def print_Power(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_Number(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_ConstantTimes(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_Add(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_Mul(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_Div(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_Chain(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_Trig(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_Alternative(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def print_DontKnow(self, rule):
        self.lines.append(self.level * "\t" + repr(rule))

    def finalize(self):
        return "\n".join(self.lines)

class IndentPrinter(DiffPrinter):
    def append(self, text):
        self.lines.append(self.level * "\t" + text)

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
            self.append("The derivative of a constant times a function is the constant times the derivative of the function.")
            with self.new_level():
                self.print_rule(rule.substep)
            self.append("The result is: {}".format(self.format_math(diffmanually(rule))))

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

            fnames = functionnames(len(rule.terms))
            ruleform = []
            for index in range(len(rule.terms)):
                buf = []
                for i in range(len(rule.terms)):
                    if i == index:
                        buf.append(fnames[i]+"\\prime")
                    else:
                        buf.append(fnames[i])
                ruleform.append("*".join(buf))
            self.append("The form here is " + " + ".join(ruleform))

            for fname, term, substep in zip(fnames, rule.terms, rule.substeps):
                self.append(fname + " = " + str(term))
                self.append("To find " + fname + "\\prime:")
                with self.new_level():
                    self.print_rule(substep)

            self.append("The result is: " + self.format_math(diffmanually(rule)))

    def print_Div(self, rule):
        with self.new_step():
            f, g = rule.numerator, rule.denominator
            fp, gp = f.diff(), g.diff()
            x = rule.symbol
            ff = sympy.Function("f")(x)
            gg = sympy.Function("g")(x)
            qrule_left = sympy.Derivative(ff / gg)
            qrule_right = sympy.ratsimp(sympy.diff(sympy.Function("f")(x) / sympy.Function("g")(x)))
            qrule = Equals(qrule_left, qrule_right)
            self.append("Apply the quotient rule:")
            self.append("The quotient rule is:")
            self.append(self.format_math_display(qrule))
            self.append("{} and {}.".format(self.format_math(Equals(ff, f)),
                                            self.format_math(Equals(gg, g))))
            self.append("To find {}:".format(self.format_math(ff.diff())))
            with self.new_level():
                self.print_rule(rule.numerstep)
            self.append("To find {}:".format(self.format_math(gg.diff())))
            with self.new_level():
                self.print_rule(rule.denomstep)
            self.append("Now plug in to the quotient rule:")
            self.append(self.format_math(diffmanually(rule)))

    def print_Chain(self, rule):
        self.print_rule(rule.substep)
        with self.new_step():
            self.append("Then, apply the chain rule. Multiply by d/dx {}:".format(
                self.format_math(rule.inner)))
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
                self.format_math_display(Equals(sympy.Derivative(rule.f),
                                                diffmanually(rule)))))

    def print_Alternative(self, rule):
        with self.new_step():
            self.append("There are multiple ways to do this derivative.")
            self.append("One way:")
            with self.new_level():
                self.print_rule(rule.alternatives[0])

    def print_DontKnow(self, rule):
        with self.new_step():
            self.append("Don't know the steps in finding this derivative.")
            self.append("But the derivative is")
            self.append(self.format_math_display(diffmanually(rule)))

class LaTeXPrinter(IndentPrinter):
    def format_math(self, math):
        return sympy.latex(math)

class HTMLPrinter(LaTeXPrinter):
    def __init__(self, rule):
        super(HTMLPrinter, self).__init__(rule)
        self.lines = ['<ol>']
        self.print_rule(rule)

    def format_math(self, math):
        return '<script type="math/tex; mode=inline">' + sympy.latex(math) + '</script>'

    def format_math_display(self, math):
        return '<script type="math/tex; mode=display">' + sympy.latex(math) + '</script>'

    @contextmanager
    def new_level(self):
        self.level += 1
        self.lines.append(self.level * '    ' + '<ol>')
        yield
        self.lines.append(self.level * '    ' + '</ol>')
        self.level -= 1

    @contextmanager
    def new_step(self):
        self.lines.append(self.level * '    ' + '<li>')
        yield self.level
        self.lines.append(self.level * '    ' + '</li>')

    @contextmanager
    def new_collapsible(self):
        self.lines.append(self.level * '    ' + '<div class="collapsible">')
        yield self.level
        self.lines.append(self.level * '    ' + '</div>')

    def append(self, text):
        self.lines.append((self.level + 1) * '    ' + '<p>{}</p>'.format(text))

    def append_header(self, text):
        self.lines.append((self.level + 1) * '    ' + '<h2>{}</h2>'.format(text))

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
        if answer:
            simp = sympy.simplify(sympy.trigsimp(answer))
            if simp != answer:
                with self.new_step():
                    self.append("Now simplify:")
                    self.append(self.format_math_display(simp))
        self.lines.append('</ol>')
        return '\n'.join(self.lines)

def printer(rule):
    a = HTMLPrinter(rule)
    return a.finalize()

def steps(diff, symbol=sympy.Symbol('x')):
    return printer(diffsteps(diff, symbol))
