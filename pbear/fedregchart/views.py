from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django import forms

import datetime
from urllib2 import quote
from math import log10, pow
from pygooglechart import Chart, Axis, SimpleLineChart

from fedregfeed.utils import fetch_page


#--------------------------------------------------------------
class SearchForm(forms.Form):
    search_term = forms.CharField(max_length=100)
   
    # start_year = forms.IntegerField("Start Year")
    #end_year = forms.IntegerField("End Year")

#--------------------------------------------------------------
def generate_chart_url(search_term, start_year, end_year):
    ''' returns url for chart after querying FR API '''
    
    year_range=range(start_year,end_year + 1)
    month_range=range(1, 13)
    base_url = "http://api.federalregister.gov/v1/articles.json" # fr api base url
    base_url_plus_search_term = base_url + "?conditions[term]=" + search_term    
    count = []
    
    for y in year_range:
    #    for m in month_range:
 #       if m < 12:
            # the following incorrectly includes first day of following month ... should do with datetime.date object instead
    #        date_conditions = "conditions[publication_date][gte]=1/" + str(m) + "/" + str(y) + "&conditions[publication_date][lte]=" + str(m+1) + "/1/" + str(y) 
  #      else:
   #         date_conditions = "conditions[publication_date][gte]=1/" + str(m) + "/" + str(y) + "&conditions[publication_date][lte]=12/31/" + str(y)
        date_conditions = "conditions[publication_date][year]=" + str(y)
        url = base_url_plus_search_term + "&" + date_conditions 
        url = quote(url, safe='/:+=?&"|')
        print "url", url
        search_result = fetch_page(url) # request page
        if search_result:  
            count.append(int(search_result['count']))
            print "count:", search_result['count']
        
    print "(in chart) count:", count

    # set up chart to display
    if max(count) < 100:
        left_axis_step = 10
        max_y = 100
    else:
        left_axis_step = int(pow(10, int(log10(max(count)))) / 10) 
        max_y = (int(max(count) / left_axis_step) * left_axis_step) + (left_axis_step * 2)
    print "left", left_axis_step, "max_y", max_y
    print "max_y", max_y
    left_axis = range(0, max_y + left_axis_step, left_axis_step)
    left_axis[0] = ""
    bottom_axis = year_range # need to fix to account for months
    chart = SimpleLineChart(600, 300, y_range=[0, max_y])
    chart.set_colours(['0000FF'])
    chart.set_axis_labels(Axis.LEFT, left_axis)
    chart.set_axis_labels(Axis.BOTTOM, bottom_axis)
    chart.set_grid(0, max(10, int(left_axis_step / 10)), 5, 5)
    chart.add_data(count)
    chart_url = chart.get_url()
       
    return chart_url
   
   
#--------------------------------------------------------------   
def show_chart(request, **kwargs):
    '''display a chart of number of FR items per month'''

    if request.method == 'POST': # If the form has been submitted...
        form = SearchForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            search_term = form.cleaned_data['search_term']
   
            #start_year = form.cleaned_data['start_year']
            #end_year = form.cleaned_data['end_year']               
   
            start_year=1994
            end_year=2011
                    
            chart_url = generate_chart_url(search_term, start_year, end_year)
            
            return render_to_response('chart.html', {"form":form, "search_term": search_term, "chart_url": chart_url}, context_instance=RequestContext(request))

    else:
                # following three vars should be passed in as kwargs
     #           search_term = kwargs['search_term'] # '\"polar bear\"|\"polar bears\"' 
      #          start_year = kwargs['start_year'] # 1994
       #         end_year = kwargs['end_year']
        try:
            search_term = kwargs['search_term']
            end_year = kwargs['end_year']
            start_year = kwargs['start_year']
            chart_url = generate_chart_url(search_term, start_year, end_year)
        except KeyError:
            search_term = None
            chart_url = None
            
        form = SearchForm() # An unbound form

    return render_to_response('chart.html', {
        'form': form, "search_term": search_term, "chart_url": chart_url
    }, context_instance=RequestContext(request))
   
