from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template.loader import render_to_string
from django.utils import simplejson
from django import forms
import django

from google.appengine.api import users
from google.appengine.runtime import DeadlineExceededError

import sympy
from logic.utils import Eval
from logic.logic import SymPyGamma, mathjax_latex
from logic.resultsets import get_card, find_result_set

import settings
import models

import os
import random
import json
import urllib
import urllib2
import datetime
import traceback

LIVE_URL = '<a href="http://live.sympy.org">SymPy Live</a>'
LIVE_PROMOTION_MESSAGES = [
    'Need more control? Try ' + LIVE_URL + '.',
    'Want a full Python shell? Use ' + LIVE_URL + '.',
    'Experiment with SymPy at ' + LIVE_URL + '.',
    'Want to compute something more complicated?' +
    ' Try a full Python/SymPy console at ' + LIVE_URL + '.'
]

EXAMPLES = [
    ('Arithmetic', [
        ['Fractions', [('Simplify fractions', '242/33'),
                       ('Rationalize repeating decimals', '0.[123]')]],
        ['Approximations', ['pi', 'E', 'exp(pi)']],
    ]),
    ('Algebra', [
        [None, ['x', '(x+2)/((x+3)(x-4))', 'simplify((x**2 - 4)/((x+3)(x-2)))']],
        ['Polynomial and Rational Functions', [
            ('Polynomial division', 'div(x**2 - 4 + x, x-2)'),
            ('Greatest common divisor', 'gcd(2*x**2 + 6*x, 12*x)'),
            ('&hellip;and least common multiple', 'lcm(2*x**2 + 6*x, 12*x)'),
            ('Factorization', 'factor(x**4/2 + 5*x**3/12 - x**2/3)'),
            ('Multivariate factorization', 'factor(x**2 + 4*x*y + 4*y**2)'),
            ('Symbolic roots', 'solve(x**2 + 4*x*y + 4*y**2)'),
            'solve(x**2 + 4*x*y + 4*y**2, y)',
            ('Complex roots', 'solve(x**2 + 4*x + 181, x)'),
            ('Irrational roots', 'solve(x**3 + 4*x + 181, x)'),
            ('Systems of equations', 'solve_poly_system([y**2 - x**3 + 1, y*x], x, y)'),
        ]],
    ]),
    ('Trigonometry', [
        [None, ['sin(2x)', 'tan(1 + x)']],
    ]),
    ('Calculus', [
        ['Limits', ['limit(tan(x), x, pi/2)', 'limit(tan(x), x, pi/2, dir="-")']],
        ['Derivatives', [
            ('Derive the product rule', 'diff(f(x)*g(x)*h(x))'),
            ('&hellip;as well as the quotient rule', 'diff(f(x)/g(x))'),
            ('Get steps for derivatives', 'diff((sin(x) * x^2) / (1 + tan(cot(x))))'),
            ('Multiple ways to derive functions', 'diff(cot(xy), y)'),
            ('Implicit derivatives, too', 'diff(y(x)^2 - 5sin(x), x)'),
        ]],
        ['Integrals', [
            'integrate(tan(x))',
            ('Multiple variables', 'integrate(2*x + y, y)'),
            ('Limits of integration', 'integrate(2*x + y, (x, 1, 3))'),
            'integrate(2*x + y, (x, 1, 3), (y, 2, 4))',
            ('Improper integrals', 'integrate(tan(x), (x, 0, pi/2))'),
            ('Exact answers', 'integrate(1/(x**2 + 1), (x, 0, oo))'),
            ('Get steps for integrals', 'integrate(exp(x) / (1 + exp(2x)))'),
            'integrate(1 /((x+1)(x+3)(x+5)))',
            'integrate((2x+3)**7)'
        ]],
        ['Series', [
            'series(sin(x), x, pi/2)',
        ]],
    ]),
    ('Number Theory', [
        [None, [
            '1006!',
            'factorint(12321)',
            ('Calculate the 42<sup>nd</sup> prime', 'prime(42)'),
            (r'Calculate \( \varphi(x) \), the Euler totient function', 'totient(42)'),
            'isprime(12321)',
            ('First prime greater than 42', 'nextprime(42)'),
        ]],
        ['Diophantine Equations', [
            'diophantine(x**2 - 4*x*y + 8*y**2 - 3*x + 7*y - 5)',
            'diophantine(2*x + 3*y - 5)',
            'diophantine(3*x**2 + 4*y**2 - 5*z**2 + 4*x*y - 7*y*z + 7*z*x)'
        ]]
    ]),
    ('Discrete Mathematics', [
        ['Boolean Logic', [
            '(x | y) & (x | ~y) & (~x | y)',
            'x & ~x'
        ]],
        ['Recurrences', [
            ('Solve a recurrence relation', 'rsolve(y(n+2)-y(n+1)-y(n), y(n))'),
            ('Specify initial conditions', 'rsolve(y(n+2)-y(n+1)-y(n), y(n), {y(0): 0, y(1): 1})')
        ]],
        ['Summation', [
            'Sum(k,(k,1,m))',
            'Sum(x**k,(k,0,oo))',
            'Product(k**2,(k,1,m))',
            'summation(1/2**i, (i, 0, oo))',
            'product(i, (i, 1, k), (k, 1, n))'
        ]]
    ]),
    ('Plotting', [
        [None, ['plot(sin(x) + cos(2x))',
                ('Multiple plots', 'plot([x, x^2, x^3, x^4])'),
                ('Polar plots', 'plot(r=1-sin(theta))'),
                ('Parametric plots', 'plot(x=cos(t), y=sin(t))'),
                ('Multiple plot types', 'plot(y=x,y1=x^2,r=cos(theta),r1=sin(theta))')]],
    ]),
    ('Miscellaneous', [
        [None, [('Documentation for functions', 'factorial2'),
                'sympify',
                'bernoulli']],
    ]),
]

class MobileTextInput(forms.widgets.TextInput):
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['autocorrect'] = 'off'
        attrs['autocapitalize'] = 'off'
        return super(MobileTextInput, self).render(name, value, attrs)

class SearchForm(forms.Form):
    i = forms.CharField(required=False, widget=MobileTextInput())

def authenticate(view):
    def _wrapper(request, **kwargs):
        user = users.get_current_user()
        result = view(request, user, **kwargs)

        try:
            template, params = result
        except ValueError:
            return result

        if user:
            params['auth_url'] = users.create_logout_url("/")
            params['auth_message'] = "Logout"
        else:
            params['auth_url'] = users.create_login_url("/")
            params['auth_message'] = "Login"
        return template, params
    return _wrapper

def app_version(view):
    def _wrapper(request, **kwargs):
        result = view(request, **kwargs)
        version, deployed = os.environ['CURRENT_VERSION_ID'].split('.')
        deployed = datetime.datetime.fromtimestamp(long(deployed) / pow(2, 28))
        deployed = deployed.strftime("%d/%m/%y %X")

        try:
            template, params = result
            params['app_version'] = version
            params['app_deployed'] = deployed
            return render_to_response(template, params)
        except ValueError:
            return result
    return _wrapper

@app_version
@authenticate
def index(request, user):
    form = SearchForm()

    if user:
        history = models.Query.query(models.Query.user_id==user.user_id())
        history = history.order(-models.Query.date).fetch(10)
    else:
        history = None

    return ("index.html", {
        "form": form,
        "MEDIA_URL": settings.MEDIA_URL,
        "main_active": "selected",
        "history": history,
        "examples": EXAMPLES
        })

@app_version
@authenticate
def input(request, user):
    if request.method == "GET":
        form = SearchForm(request.GET)
        if form.is_valid():
            input = form.cleaned_data["i"]

            if input.strip().lower() in ('random', 'example', 'random example'):
                return redirect('/random')

            g = SymPyGamma()
            r = g.eval(input)

            if not r:
                r = [{
                    "title": "Input",
                    "input": input,
                    "output": "Can't handle the input."
                }]

            if (user and not models.Query.query(
                    models.Query.text==input,
                    models.Query.user_id==user.user_id()).get()):
                query = models.Query(text=input, user_id=user.user_id())
                query.put()
            elif not models.Query.query(models.Query.text==input).get():
                query = models.Query(text=input, user_id=None)
                query.put()


            # For some reason the |random tag always returns the same result
            return ("result.html", {
                "input": input,
                "result": r,
                "form": form,
                "MEDIA_URL": settings.MEDIA_URL,
                "promote_live": random.choice(LIVE_PROMOTION_MESSAGES)
                })

@app_version
@authenticate
def about(request, user):
    return ("about.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "about_active": "selected",
        })

def random_example(request):
    examples = []

    for category in EXAMPLES:
        for subcategory in category[1]:
            for example in subcategory[1]:
                if isinstance(example, tuple):
                    examples.append(example[1])
                else:
                    examples.append(example)

    return redirect('input/?i=' + urllib.quote(random.choice(examples)))

def _process_card(request, card_name):
    variable = request.GET.get('variable')
    expression = request.GET.get('expression')
    if not variable or not expression:
        raise Http404

    variable = urllib2.unquote(variable)
    expression = urllib2.unquote(expression)

    g = SymPyGamma()

    parameters = {}
    for key, val in request.GET.items():
        parameters[key] = ''.join(val)

    return g, variable, expression, parameters


def eval_card(request, card_name):
    g, variable, expression, parameters = _process_card(request, card_name)

    try:
        result = g.eval_card(card_name, expression, variable, parameters)
    except ValueError as e:
        return HttpResponse(json.dumps({
            'error': e.message
        }), mimetype="application/json")
    except DeadlineExceededError:
        return HttpResponse(json.dumps({
            'error': 'Computation timed out.'
        }), mimetype="application/json")
    except:
        trace = traceback.format_exc(5)
        return HttpResponse(json.dumps({
            'error': ('There was an error in Gamma. For reference'
                      'the last five traceback entries are: ' + trace)
        }), mimetype="application/json")

    return HttpResponse(json.dumps(result), mimetype="application/json")

def get_card_info(request, card_name):
    g, variable, expression, _ = _process_card(request, card_name)

    try:
        result = g.get_card_info(card_name, expression, variable)
    except ValueError as e:
        return HttpResponse(json.dumps({
            'error': e.message
        }), mimetype="application/json")
    except DeadlineExceededError:
        return HttpResponse(json.dumps({
            'error': 'Computation timed out.'
        }), mimetype="application/json")
    except:
        trace = traceback.format_exc(5)
        return HttpResponse(json.dumps({
            'error': ('There was an error in Gamma. For reference'
                      'the last five traceback entries are: ' + trace)
        }), mimetype="application/json")

    return HttpResponse(json.dumps(result), mimetype="application/json")

def get_card_full(request, card_name):
    g, variable, expression, parameters = _process_card(request, card_name)

    try:
        card_info = g.get_card_info(card_name, expression, variable)
        result = g.eval_card(card_name, expression, variable, parameters)
        card_info['card'] = card_name
        card_info['cell_output'] = result['output']

        html = render_to_string('card.html', {
            'cell': card_info,
            'input': expression
        })
    except ValueError as e:
        card_info = g.get_card_info(card_name, expression, variable)
        return HttpResponse(render_to_string('card.html', {
            'cell': {
                'title': card_info['title'],
                'input': card_info['input'],
                'card': card_name,
                'variable': variable,
                'error': e.message
            },
            'input': expression
        }), mimetype="text/html")
    except DeadlineExceededError:
        return HttpResponse('Computation timed out.',
                            mimetype="text/html")
    except:
        trace = traceback.format_exc(5)
        return HttpResponse(render_to_string('card.html', {
            'cell': {
                'card': card_name,
                'variable': variable,
                'error': trace
            },
            'input': expression
        }), mimetype="text/html")

    response = HttpResponse(html, mimetype="text/html")
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'

    return response

def remove_query(request, qid):
    user = users.get_current_user()

    if user:
        query = models.ndb.Key(urlsafe=qid).get()

        if not models.Query.query(models.Query.text==query.text):
            query.user_id = None
            query.put()
        else:
            query.key.delete()

        response = {
            'result': 'success',
        }
    else:
        response = {
            'result': 'error',
            'message': 'Not logged in or invalid user.'
        }

    return HttpResponse(json.dumps(response), mimetype='application/json')

@app_version
def view_404(request):
    return ("404.html", {})

@app_version
def view_500(request):
    return ("500.html", {})
