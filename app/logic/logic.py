import sys
import collections
from utils import Eval, latexify, topcall, arguments, removeSymPy, \
    custom_implicit_transformation, synonyms
from resultsets import find_result_set, get_card, format_by_type
from sympy import latex, series, sympify, solve, Derivative, \
    Integral, Symbol, diff, integrate
import sympy
from sympy.core.function import FunctionClass
from sympy.parsing.sympy_parser import stringify_expr, eval_expr, \
    standard_transformations, convert_xor, TokenError

PREEXEC = """from __future__ import division
from sympy import *
import sympy
x, y, z = symbols('x,y,z')
k, m, n = symbols('k,m,n', integer=True)
f, g, h = map(Function, 'fgh')"""


def mathjax_latex(obj):
    if hasattr(obj, 'as_latex'):
        tex_code = obj.as_latex()
    else:
        tex_code = latex(obj)
    return ''.join(['<script type="math/tex; mode=display">', tex_code,
                    '</script>'])


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

            return self.prepare_cards(parsed, arguments, evaluator, evaluated)

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

    def disambiguate(self, arguments):
        if arguments[0] == 'factor':
            if arguments.args and isinstance(arguments.args[0], sympy.Number):
                return ('factorint({})'.format(arguments.args[0]),
                        "<var>factor</var> factors polynomials, while <var>factorint</var> factors integers.")
        return None

    def eval_input(self, s):
        namespace = {}
        exec PREEXEC in {}, namespace
        evaluator = Eval(namespace)
        # change to True to spare the user from exceptions:
        if not len(s):
            return None

        transformations = []
        transformations.append(synonyms)
        transformations.extend(standard_transformations)
        transformations.extend((convert_xor, custom_implicit_transformation))
        local_dict = {}
        global_dict = {}
        exec 'from sympy import *' in global_dict
        parsed = stringify_expr(s, local_dict, global_dict, transformations)
        evaluated = eval_expr(parsed, local_dict, global_dict)
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

        if first_func_name:
            first_func = evaluator.get(first_func_name)
            is_function = (
                first_func and
                not isinstance(first_func, FunctionClass) and
                not isinstance(first_func, sympy.Atom) and
                first_func_name and first_func_name[0].islower())

        if is_applied:
            convert_input, cards, handles_function = find_result_set(arguments[0], evaluated)
        else:
            convert_input, cards, handles_function = find_result_set(None, evaluated)

        components = convert_input(arguments, evaluated)
        if 'input_evaluated' in components:
            evaluated = components['input_evaluated']

        evaluator.set('input_evaluated', evaluated)

        return components, cards, evaluated, handles_function, is_function and is_applied

    def prepare_cards(self, parsed, arguments, evaluator, evaluated):
        input_repr = repr(evaluated)
        components, cards, evaluated, handles_function, is_function = self.get_cards(arguments, evaluator, evaluated)

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
            "output": latex_input,
            "num_variables": len(components['variables']),
            "variables": map(repr, components['variables']),
            "variable": repr(components['variable'])
        })

        # If no result cards were found, but the top-level call is to a
        # function, then add a special result card to show the result
        if not cards and not components['variable'] and is_function:
            result.append({
                'title': 'Result',
                'input': removeSymPy(parsed),
                'output': format_by_type(evaluated, mathjax_latex)
            })
        else:
            input_repr = repr(evaluated)
            var = components['variable']

            # If the expression is something like 'lcm(2x, 3x)', display the
            # result of the function before the rest of the cards
            if is_function and not handles_function:
                result.append(
                    {"title": "Result", "input": "",
                     "output": mathjax_latex(evaluated)})

            line = "simplify(input_evaluated)"
            simplified = evaluator.eval(line,
                                        use_none_for_exceptions=True,
                                        repr_expression=False)
            if (simplified != None and
                simplified != evaluated):
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
                        'input': card.format_input(input_repr, components),
                        'pre_output': latex(
                            card.pre_output_function(evaluated, var)),
                        'parameters': card.card_info.get('parameters', [])
                    })
                except (SyntaxError, ValueError) as e:
                    pass
        return result

    def get_card_info(self, card_name, expression, variable):
        card = get_card(card_name)

        if not card:
            raise KeyError

        _, arguments, evaluator, evaluated = self.eval_input(expression)
        variable = sympy.Symbol(variable)
        components, cards, evaluated,  _, _ = self.get_cards(arguments, evaluator, evaluated)
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

        components, cards, evaluated,  _, _ = self.get_cards(arguments, evaluator, evaluated)

        components['variable'] = variable

        result = card.eval(evaluator, components, parameters)

        return {
            'value': repr(result),
            'output': card.format_output(result, mathjax_latex)
        }
