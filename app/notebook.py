#from __future__ import print_function
from __future__ import absolute_import
from django.shortcuts import render
from google.appengine.ext import ndb

from app.models import Notebook
from sympy import *
import json
from string import find

from urllib import unquote
import ast
from copy import copy

#---------------------------------------------------------------
# sample.ipynb is a file initially used to write the result's 
# notebook to the database.
#---------------------------------------------------------------

#plot = '%matplotlib inline'


#notebook_format = { "metadata": {"name": ""}, "nbformat": 3, "nbformat_minor": 0, "worksheets": [{ "cells": [],"metadata": {} }]}

#code_cell = {"cell_type": "code",  "input": [], "language": "python", "metadata": {}, "outputs": [{ "output_type": "stream","stream": "stdout", "text": []}], "prompt_number": 1 }, 

#markdown_cell = {"cell_type": "markdown","metadata": {},"source":[]}, 

#heading_cell = {"cell_type": "heading","level": 3,"metadata": {},"source": []},



def result_pass(request):

    ''' This function parses and creates the result's json for nbviewer '''
    notebook_format = { "metadata": {"name": ""}, "nbformat": 3, "nbformat_minor": 0, "worksheets": [{ "cells": [],"metadata": {} }]}
    notebook = notebook_format
    result = request.GET.get('result')
    result = unquote(result)
    result = ast.literal_eval(result)

    #----------------------------------------------------------
    # this is in no way completed. we need to implement plotting  
    # and cards. cards can be implemented by using exec 
    # statements like 
    # a = ''' import sympy
    #         x = Symbol('x')
    #         series(tan(x + 1), x, 0, 10)
    # for plotting we can use existing support of matplotlib on
    # Google App engine.
    #-------------------------------------------------------------
    
    for cell in result:
        heading_cell = {"cell_type": "heading","level": 3,"metadata": {},"source": []},
        title = heading_cell[0]
        title['level'] = 3
        a = str(cell['title'])
        title['source'] = [ a ]
        notebook['worksheets'][0]['cells'].append(title)    
        if 'ambiguity' in cell.keys():
            pass
        elif 'card' in cell.keys():    
            pass
            
        else:
    
            if 'input' in cell.keys():
                #---------------------------------------------------------------------
                # i have tried defining the variables beforehand but somehow 
                # these tuples are not getting copied. they are just the pointers to 
                # the initial variables.
                #---------------------------------------------------------------------
                heading_cell = {"cell_type": "heading","level": 3,"metadata": {},"source": []},
                inputs = heading_cell[0]
                inputs['level'] = 3
                inputs['source'] = [ str(cell['input']) ]
                notebook['worksheets'][0]['cells'].append(inputs)
            if 'output' in cell.keys():
                markdown_cell = {"cell_type": "markdown","metadata": {},"source":[]}, 
                output = markdown_cell[0]
                if 'href' in cell['output']:
                    pass
                else:
                    start = find(cell['output'], '>')
                    end = find(cell['output'], '</')
                    mathjax = cell['output'][ start+1: end ]
                            
                    mathjax = '$$' + str(mathjax) + '$$'  
                    output['source'] = [mathjax]
                    notebook['worksheets'][0]['cells'].append(output)
                    
            if 'pre_output' in cell.keys():
                heading_cell = {"cell_type": "heading","level": 3,"metadata": {},"source": []},
                pre_output = heading_cell[0]
                if cell['pre_output'] != '':
                    mathjax1 = cell['pre_output']
                    mathjax1 = mathjax1.replace('\\\\','\\')
                    mathjax1 = '$$' + str(mathjax1) + '$$'
                    output['source'] = [mathjax1]
                    notebook['worksheets'][0]['cells'].append(pre_output)
                        
        notebook = json.dumps(notebook)         
        
        return render(request, 'result_notebook.html',
                      {'result': result,
                       'notebook': notebook})
    
    
    
    
    
    
    
    
    
    
    
    
    
