'''
documentation/views.py v0.1 121008

Created on 121008

@author: edwin

'''
#TODO: fix SVG files.
#TODO: add workflows (make metasystem, make pool, ...)
#TODO: explain how performance is saved, incl conditions for tr/eq

from django.shortcuts import render

from metasystem.parameters.fields import _Param

from system.views import OUTPUT_FORMATS


def documentation(request):
    '''
    View that shows terminology and doc strings
    '''
    docs = []
    for key, params in OUTPUT_FORMATS.items():
        if 'verbose' in params:
            docs.append((key, params['verbose']))
    return render(request, 'documentation.html', {'docs': docs})


def param_documentation(request, par_type):
    '''
    View that shows terminology and doc strings
    '''
    docs = _Param.get_doc(par_type)
    return render(request, 'param_documentation.html', 
            {'par_type': par_type,
             'docs': docs})
