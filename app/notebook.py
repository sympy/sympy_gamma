from __future__ import absolute_import
from django.shortcuts import render
from sympy import *
from string import find
from urllib import unquote
from copy import copy
from django.template import defaultfilters
from django.utils import simplejson
from app.logic import Eval, SymPyGamma
import json
import ast

notebook_format = { "metadata": {"name": ""}, "nbformat": 3, "nbformat_minor": 0, "worksheets": [{ "cells": [],"metadata": {} }]}
code_cell = {"cell_type": "code",  "input": [], "language": "python", "metadata": {}, "outputs": [{ "output_type": "stream","stream": "stdout", "text": []}], "prompt_number": 1 },
markdown_cell = {"cell_type": "markdown","metadata": {},"source":[]},
heading_cell = {"cell_type": "heading","level": 3,"metadata": {},"source": []},

def result_pass(request):
    ''' This function parses and creates the result's json for nbviewer '''
    notebook_format = { "metadata": {"name": ""}, "nbformat": 3, "nbformat_minor": 0, "worksheets": [{ "cells": [],"metadata": {} }]}
    notebook = notebook_format
    inp = request.GET.get('i')
    #inp = unquote(inp)
    #inp = ast.literal_eval(inp)
    g = SymPyGamma()
    result = g.eval(inp)
    #----------------------------------------------------------
    # 1)this is in no way completed. we need to implement plotting
    # and cards. cards can be implemented by using exec
    # statements like
    # a = ''' import sympy
    #         x = Symbol('x')
    #         series(tan(x + 1), x, 0, 10)'''
    # for plotting we can use existing support of matplotlib on
    # Google App engine.
    # 2)Mathjax include the escaping '\\' which is originally '\'
    # so we need to parse them to display it correctly.
    #-------------------------------------------------------------
    for q in range(len(result)):
        cell = result[q]
        if 'ambiguity' in cell.keys():
            ambiguity = copy(markdown_cell[0])
            description = heading_cell[0]
            card_link = cell['ambiguity']
            link = '<p>Did you mean: <a href="/input/?i=' + str(card_link) + '>"' + str(card_link) + '</a>?</p>'
            ambiguity['source'] = link
            description['source'] = cell['description']
            notebook['worksheets'][0]['cells'].append(ambiguity)
            notebook['worksheets'][0]['cells'].append(description)
        else:
            title = copy(heading_cell[0])
            title['level'] = 3
            a = str(cell['title'])
            title['source'] = [ a ]
            notebook['worksheets'][0]['cells'].append(title)
            if 'input' in cell.keys():
                inputs = copy(heading_cell[0])
                inputs['level'] = 3
                inputs['source'] = [ str(cell['input']) ]
                notebook['worksheets'][0]['cells'].append(inputs)
            if 'output' in cell.keys():
                output = copy(markdown_cell[0])
                strip = cell['output']
                a = strip.find('>')
                strip = strip[a+1:]
                b = strip.find('<')
                strip = strip[:b]
                output['source'] = strip
                notebook['worksheets'][0]['cells'].append(output)
                if 'pre_output' in cell.keys():
                    pre_output = copy(markdown_cell[0])
                    #pre_output['source'] = correct_mathjax(cell['pre_output'])
                    pre_output['source'] = cell['pre_output']
                    notebook['worksheets'][0]['cells'].append(pre_output)
            if 'card' in cell.keys():
                if 'pre_output' in cell.keys():
                    cell_pre_output = copy(markdown_cell[0])
                    cell_pre_output['source'] = cell['pre_output']
                    notebook['worksheets'][0]['cells'].append(cell_pre_output)
            if 'cell_output' in cell.keys():
                    cell_output = copy(markdown_cell[0])
                    cell_output['source'] = cell['cell_output']
                    notebook['worksheets'][0]['cells'].append(cell_output)
            else:
                    pass

    notebook = json.dumps(notebook)
    return render(request, 'result_notebook.html',
                      {'result': result,
                       'notebook': notebook,
                       'result': result})


def html_mathjax(html_mathjax):
    ''' removes extra '\n' and '\\' in the output.'''

def correct_mathjax(mathjax):
    ''' removes extra '\n' and '\\' in the pre_output'''
