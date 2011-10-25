from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
#import numpy as np
#import matplotlib.pyplot as plt

def chart(request, **kwargs):
    '''display a chart by year of number of FR items'''
       
    return render_to_response('chart.html', kwargs, context_instance=RequestContext(request))
