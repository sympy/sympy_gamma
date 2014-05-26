from __future__ import absolute_import
from django.http import HttpResponse
from copy import copy
from app.logic import SymPyGamma
from app.views import eval_card
import json
import urllib2

#<p id="heading">SymPy</p>   #styling for notebook's headings.
#<style>
#    #heading {
#        text-align:center;
#        font-size:40px;
#        border-bottom: 1px solid black;
#    }
#</style>

def result_json(request):

    ''' IPython notebook format generator. Parses the result set and
        converts them into IPython notebook's format. '''

    notebook_format = { "metadata": {"name": ""}, "nbformat": 3, "nbformat_minor": 0, "worksheets": [{ "cells": [],"metadata": {} }]}
    code_cell = {"cell_type": "code",  "input": [], "language": "python", "metadata": {}, "outputs": [{ "output_type": "stream","stream": "stdout", "text": []}], "prompt_number": 1 },
    markdown_cell = {"cell_type": "markdown","metadata": {},"source":[]},
    heading_cell = {"cell_type": "heading","level": 3,"metadata": {},"source": []},

    exp = request.GET.get('i')
    exp = urllib2.unquote(exp)
    g = SymPyGamma()
    result = g.eval(exp)
    notebook = copy(notebook_format)

    for cell in result:
        title = copy(heading_cell[0])
        title['level'] = 3
        a = str(cell['title'])
        title['source'] = [a]
        notebook['worksheets'][0]['cells'].append(title)

        if 'input' in cell.keys():
            inputs = copy(heading_cell[0])
            inputs['level'] = 4
            inputs['source'] = [str(cell['input'])]
            notebook['worksheets'][0]['cells'].append(inputs)

        if 'output' in cell.keys():
            output = copy(markdown_cell[0])

            if 'pre_output' in cell.keys():
                if cell['pre_output'] !="":
                    pre_output = copy(markdown_cell[0])
                    pre_output['source'] = ['$$'+str(cell['pre_output'])+'$$']
                    notebook['worksheets'][0]['cells'].append(pre_output)

            if cell['output'] != "" and 'script' in cell['output']:
                output['source'] = [cell['output']]
                notebook['worksheets'][0]['cells'].append(output)

        if 'card' in cell.keys():
            if cell['card'] != 'plot':
                card_name = cell['card']
                variable = cell['var']
                parameters = {}
                if 'pre_output' in cell.keys():
                    if cell['pre_output'] != '':
                        cell_pre_output = copy(markdown_cell[0])
                        cell_pre_output['source'] = ['$$'+str(cell['pre_output'])+'$$']
                        notebook['worksheets'][0]['cells'].append(cell_pre_output)

                try:
                    card_json = g.eval_card(card_name, exp, variable, parameters)
                    #card_json = json.loads(card_json)
                    card_result = copy(markdown_cell[0])
                    card_result['source'] = [card_json['output']]
                    notebook['worksheets'][0]['cells'].append(card_result)
                except:
                    card_error = copy(markdown_cell[0])
                    card_error['source'] = ['Errored']
                    notebook['worksheets'][0]['cells'].append(card_error)
            else:
                card_plot = copy(markdown_cell[0])
                card_plot['source'] = ['Plotting is not yet implemented.']
                notebook['worksheets'][0]['cells'].append(card_plot)



        if 'cell_output' in cell.keys():
            if cell['cell_output'] != "":
                cell_output = copy(markdown_cell[0])
                cell_output['source'] = [cell['cell_output']]
                notebook['worksheets'][0]['cells'].append(cell_output)

        else:
                pass

    notebook_json = json.dumps(notebook)
    response =  HttpResponse(notebook_json, content_type = 'text/plain')

    #response['Content-Disposition'] = 'attachment; filename=gamma.ipynb'
    return response