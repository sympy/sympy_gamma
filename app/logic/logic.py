from __future__ import absolute_import
import traceback
from .utils import Eval, latexify, arguments, removeSymPy, \
    custom_implicit_transformation, synonyms, OTHER_SYMPY_FUNCTIONS, \
    close_matches
from .resultsets import find_result_set, get_card, format_by_type, \
    is_function_handled, find_learn_more_set
from sympy import latex
import sympy
from sympy.core.function import FunctionClass
from sympy.parsing.sympy_parser import stringify_expr, eval_expr, \
    standard_transformations, convert_xor, TokenError
from six.moves import map

PREEXEC = """from __future__ import division
from sympy import *
import sympy
from sympy.solvers.diophantine import diophantine
"""


def mathjax_latex(*args):
    tex_code = []
    for obj in args:
        if hasattr(obj, 'as_latex'):
            tex_code.append(obj.as_latex())
        else:
            tex_code.append(latex(obj))

    tag = '<script type="math/tex; mode=display">'
    if len(args) == 1:
        obj = args[0]
        if (isinstance(obj, sympy.Basic) and
            not obj.free_symbols and not obj.is_Integer and
            not obj.is_Float and
            obj.is_finite is not False and
            hasattr(obj, 'evalf')):
            tag = '<script type="math/tex; mode=display" data-numeric="true" ' \
                  'data-output-repr="{}" data-approximation="{}">'.format(
                      repr(obj), latex(obj.evalf(15)))

    tex_code = ''.join(tex_code)

    return ''.join([tag, tex_code, '</script>'])


class SymPyGamma(object):

    def eval(self, s):
        result = None

        try:
            result = self.eval_input(s)
        except TokenError:
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": "Invalid input"}
            ]
        except Exception as e:
            return self.handle_error(s, e)

        if result:
            parsed, arguments, evaluator, evaluated = result

            cards = []

            close_match = close_matches(s, sympy.__dict__)
            if close_match:
                cards.append({
                    "ambiguity": close_match,
                    "description": ""
                })

            try:
                cards.extend(self.prepare_cards(parsed, arguments, evaluator, evaluated))
            except ValueError as e:
                return self.handle_error(s, e)

            return cards

    def handle_error(self, s, e):
        if isinstance(e, SyntaxError):
            error = {
                "msg": str(e),
                "offset": e.offset
            }
            if e.text:
                error["input_start"] = e.text[:e.offset]
                error["input_end"] = e.text[e.offset:]
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "exception_info": error}
            ]
        elif isinstance(e, ValueError):
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": str(e)}
            ]
        else:
            trace = traceback.format_exc()
            trace = ("There was an error in Gamma.\n"
                     "For reference, the stack trace is:\n\n" + trace)
            return [
                {"title": "Input", "input": s},
                {"title": "Error", "input": s, "error": trace}
            ]

    def disambiguate(self, arguments):
        if arguments[0] == 'factor':
            if arguments.args and isinstance(arguments.args[0], sympy.Number):
                return ('factorint({})'.format(arguments.args[0]),
                        "<var>factor</var> factors polynomials, while <var>factorint</var> factors integers.")
        return None

    def eval_input(self, s):
        namespace = {}
        exec(PREEXEC, {}, namespace)

        def plot(f=None, **kwargs):
            """Plot functions. Not the same as SymPy's plot.

            This plot function is specific to Gamma. It has the following syntax::

                plot([x^2, x^3, ...])

            or::

                plot(y=x,y1=x^2,r=sin(theta),r1=cos(theta))

            ``plot`` accepts either a list of single-variable expressions to
            plot or keyword arguments indicating expressions to plot. If
            keyword arguments are used, the plot will be polar if the keyword
            argument starts with ``r`` and will be an xy graph otherwise.

            Note that Gamma will cut off plot values above and below a
            certain value, and that it will **not** warn the user if so.

            """
            pass
        namespace.update({
            'plot': plot,  # prevent textplot from printing stuff
            'help': lambda f: f
        })

        evaluator = Eval(namespace)
        # change to True to spare the user from exceptions:
        if not len(s):
            return None

        transformations = []
        transformations.append(synonyms)
        transformations.extend(standard_transformations)
        transformations.extend((convert_xor, custom_implicit_transformation))
        parsed = stringify_expr(s, {}, namespace, transformations)
        try:
            evaluated = eval_expr(parsed, {}, namespace)
        except SyntaxError:
            raise
        except Exception as e:
            raise ValueError(str(e))
        input_repr = repr(evaluated)
        namespace['input_evaluated'] = evaluated

        return parsed, arguments(parsed, evaluator), evaluator, evaluated

    def get_cards(self, arguments, evaluator, evaluated):
        first_func_name = arguments[0]
        # is the top-level function call to a function such as factorint or
        # simplify?
        is_function = False
        # is the top-level function being called?
        is_applied = arguments.args or arguments.kwargs

        first_func = evaluator.get(first_func_name)
        is_function = (
            first_func and
            not isinstance(first_func, FunctionClass) and
            not isinstance(first_func, sympy.Atom) and
            first_func_name and first_func_name[0].islower() and
            not first_func_name in OTHER_SYMPY_FUNCTIONS)

        if is_applied:
            convert_input, cards = find_result_set(arguments[0], evaluated)
        else:
            convert_input, cards = find_result_set(None, evaluated)

        components = convert_input(arguments, evaluated)
        if 'input_evaluated' in components:
            evaluated = components['input_evaluated']

        evaluator.set('input_evaluated', evaluated)

        return components, cards, evaluated, (is_function and is_applied)

    def prepare_cards(self, parsed, arguments, evaluator, evaluated):
        components, cards, evaluated, is_function = self.get_cards(arguments, evaluator, evaluated)

        if is_function:
            latex_input = ''.join(['<script type="math/tex; mode=display">',
                                   latexify(parsed, evaluator),
                                   '</script>'])
        else:
            latex_input = mathjax_latex(evaluated)

        result = []

        ambiguity = self.disambiguate(arguments)
        if ambiguity:
            result.append({
                "ambiguity": ambiguity[0],
                "description": ambiguity[1]
            })

        result.append({
            "title": "SymPy",
            "input": removeSymPy(parsed),
            "output": latex_input
        })

        if cards:
            if any(get_card(c).is_multivariate() for c in cards):
                result[-1].update({
                    "num_variables": len(components['variables']),
                    "variables": list(map(repr, components['variables'])),
                    "variable": repr(components['variable'])
                })

        # If no result cards were found, but the top-level call is to a
        # function, then add a special result card to show the result
        if not cards and not components['variable'] and is_function:
            result.append({
                'title': 'Result',
                'input': removeSymPy(parsed),
                'output': format_by_type(evaluated, arguments, mathjax_latex)
            })
        else:
            var = components['variable']

            # If the expression is something like 'lcm(2x, 3x)', display the
            # result of the function before the rest of the cards
            if is_function and not is_function_handled(arguments[0]):
                result.append(
                    {"title": "Result", "input": "",
                     "output": format_by_type(evaluated, arguments, mathjax_latex)})

            line = "simplify(input_evaluated)"
            simplified = evaluator.eval(line,
                                        use_none_for_exceptions=True,
                                        repr_expression=False)
            if (simplified != None and
                simplified != evaluated and
                arguments.args and
                len(arguments.args) > 0 and
                simplified != arguments.args[0]):
                result.append(
                    {"title": "Simplification", "input": repr(simplified),
                     "output": mathjax_latex(simplified)})
            elif arguments.function == 'simplify':
                result.append(
                    {"title": "Simplification", "input": "",
                     "output": mathjax_latex(evaluated)})

            for card_name in cards:
                card = get_card(card_name)

                if not card:
                    continue

                try:
                    result.append({
                        'card': card_name,
                        'var': repr(var),
                        'title': card.format_title(evaluated),
                        'input': card.format_input(repr(evaluated), components),
                        'pre_output': latex(
                            card.pre_output_function(evaluated, var)),
                        'parameters': card.card_info.get('parameters', [])
                    })
                except (SyntaxError, ValueError) as e:
                    pass

            if is_function:
                learn_more = find_learn_more_set(arguments[0])
                if learn_more:
                    result.append({
                        "title": "Learn More",
                        "input": '',
                        "output": learn_more
                    })
        return result

    def get_card_info(self, card_name, expression, variable):
        card = get_card(card_name)

        if not card:
            raise KeyError

        _, arguments, evaluator, evaluated = self.eval_input(expression)
        variable = sympy.Symbol(variable)
        components, cards, evaluated, _ = self.get_cards(arguments, evaluator, evaluated)
        components['variable'] = variable

        return {
            'var': repr(variable),
            'title': card.format_title(evaluated),
            'input': card.format_input(repr(evaluated), components),
            'pre_output': latex(card.pre_output_function(evaluated, variable))
        }

    def eval_card(self, card_name, expression, variable, parameters):
        card = get_card(card_name)

        if not card:
            raise KeyError

        _, arguments, evaluator, evaluated = self.eval_input(expression)
        variable = sympy.Symbol(variable)
        components, cards, evaluated, _ = self.get_cards(arguments, evaluator, evaluated)
        components['variable'] = variable
        evaluator.set(str(variable), variable)
        result = card.eval(evaluator, components, parameters)

        return {
            'value': repr(result),
            'output': card.format_output(result, mathjax_latex)
        }
