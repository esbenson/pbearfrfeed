from fedregfeed.models import FedRegDoc, Agency

from urllib2 import urlopen, quote
import json
import datetime
from math import log10, pow
from pygooglechart import Chart, Axis, SimpleLineChart, StackedHorizontalBarChart, PieChart2D
import calendar
import random
from operator import itemgetter

# --------------------------------------------------------------
# generate trophy map chart url - getting counts from FR api
# -------------------------------------------------------------------------
def generate_trophy_map_chart_url(state_counts):

    base_url = 'https://chart.googleapis.com/chart'
    map_type = "cht=map"
    map_size = "chs=" + "600x400" 
    map_states="chld=" 
    color_values = "chd=t:"
    for k,v in state_counts.iteritems():
        map_states += "US-" + k + "|"
        color_values += str(v) + ","
    map_states=map_states[:-1] #remove trailing pipe
    color_values=color_values[:-1]# remove trailing comma
    color_gradient="chco=CCCCCC,FFFFFF,0000FF" # from white to blue, on gray background   

    params = map_type + "&" + map_size + "&" + map_states + "&" + color_values + "&" + color_gradient 
    chart_url = base_url + "?" + quote(params, "&?,=|")   
    print "chart_url in generate_trophy_map_chart_url", chart_url 

    return chart_url
    

# --------------------------------------------------------------
# generate chart url of frequencies of polar bear-related FR items - getting counts from FR api
# -------------------------------------------------------------------------
def generate_freq_chart_url_from_fedreg(search_term, start_year, end_year):
    ''' returns url for chart after querying FR API '''
    
    year_range=range(start_year,end_year + 1)
    month_range=range(1, 13)
    base_url = "http://api.federalregister.gov/v1/articles.json" # fr api base url
    base_url_plus_search_term = base_url + "?conditions[term]=" + search_term    
    count = []
    
    for y in year_range:
        date_conditions = "conditions[publication_date][year]=" + str(y)
        url = base_url_plus_search_term + "&" + date_conditions 
        url = quote(url, safe='/:+=?&"|')
        print "url", url
        search_result = fetch_fedreg_results_page(url) # request page
        if search_result:  
            count.append(int(search_result['count']))
            print "count:", search_result['count']
        
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
    bottom_axis = year_range
    chart = SimpleLineChart(600, 300, y_range=[0, max_y])
    chart.set_colours(['0000FF'])
    chart.set_axis_labels(Axis.LEFT, left_axis)
    chart.set_axis_labels(Axis.BOTTOM, bottom_axis)
    chart.set_grid(0, max(10, int(left_axis_step / 10)), 5, 5)
    chart.add_data(count)
    chart_url = chart.get_url()
       
    return chart_url

# --------------------------------------------------------------
# generate chart url of frequencies of polar bear-related FR items - getting counts from local database 
# -------------------------------------------------------------------------
def generate_freq_chart_url_from_local(search_term, start_year, end_year, sizex, sizey):
    ''' returns url for chart after querying local database '''
   
    year_range=range(start_year,end_year + 1)
    month_range=range(1, 13)
    count_rules = []
    count_proprules = []
    count_notices = []
    count_presdocs = []
    count_unknown = []
    count_total = []
    today = datetime.date.today()    
        
    for y in year_range:
        start_date=datetime.date(y,1,1)
        end_date=datetime.date(y,12,31)
        year_qset = FedRegDoc.objects.filter(publication_date__range=(start_date, end_date))
        if search_term:
            year_qset = year_qset.filter(html_full_text__contains=search_term)
        count_rules.append(year_qset.filter(document_type='Rule').count())
        count_proprules.append(year_qset.filter(document_type='Proposed Rule').count())
        count_notices.append(year_qset.filter(document_type='Notice').count())
        count_presdocs.append(year_qset.filter(document_type='Presidential Document').count())
        count_unknown.append(year_qset.filter(document_type='Document of Unknown Type').count())
        count_total.append(count_unknown[-1] + count_presdocs[-1] + count_rules[-1] + count_proprules[-1] + count_notices[-1])

    # set up chart axis parameters
    largest_y = max(count_total)
    left_axis_step = int(pow(10, int(log10(largest_y)))) 
    max_y = (int(largest_y / left_axis_step) * left_axis_step) + (left_axis_step * 2)
    left_axis = range(0, max_y + left_axis_step, left_axis_step)
    left_axis[0] = ""
    bottom_axis = year_range

    # generate chart url
    chart = SimpleLineChart(sizex, sizey, y_range=[0, max_y])
    chart.set_axis_labels(Axis.LEFT, left_axis)
    chart.set_axis_labels(Axis.BOTTOM, bottom_axis)
    chart.set_grid(0, max(10, int(left_axis_step / 10)), 5, 5)
    chart.set_colours(['0000FF', '00FF00', 'FF0000', 'FFFF00', '00FFFF', 'aaaaaa'])
    chart.set_legend(['Rules', 'Proposed Rules', 'Notices', 'Presidential Docs', 'Unknown', 'Total'])
    chart.add_data(count_rules)
    chart.add_data(count_proprules)
    chart.add_data(count_notices)
    chart.add_data(count_presdocs)
    chart.add_data(count_unknown)
    chart.add_data(count_total)
    chart_url = chart.get_url()
       
    return chart_url

#-------------------------------------------------------------------------------
# generate url for google pie chart of source populations for trophy imports
#-------------------------------------------------------------------------------    
def generate_pie_chart_source_popn(trophies):
    source_popn_counts = {}
    chart_data_labels = []
    chart_data = []
    chart_labels = []
    total_app_count = 0
         
    # count permit apps for each polar bear source population
    for t in trophies:
        if t['app_popn']:
            try:
                source_popn_counts[t['app_popn']] += 1
                total_app_count += 1                
            except KeyError:
                source_popn_counts[t['app_popn']] = 1
    
    # generate sortedlists of chart data and labels
    for k,v in source_popn_counts.iteritems():
        chart_data_labels.append([k, v])
    chart_data_labels.sort(key=itemgetter(1))
    print "sorted chart_data_labels: ", chart_data_labels    
    for c in chart_data_labels:
        percent=float(c[1])/total_app_count
        chart_labels.append(c[0] + " (" + str(c[1]) + " / " + "{:.2%})".format(percent))
        chart_data.append(percent)
 
    # assemble chart url
    chart = PieChart2D(700,250)
    chart.add_data(chart_data)
    chart.set_colours(['0000FF'])
    chart.set_pie_labels(chart_labels)
    chart_url = chart.get_url()
    
    return chart_url

# ---------------------------------------------------------------
#    generate chart of trophy applications by year
# ---------------------------------------------------------------
def generate_trophy_freq_chart_url(trophies):

    counts = []
    lancaster_counts = []
    nbeaufort_counts = []
    sbeaufort_counts = []
    other_counts = []
    lancaster_years_with_counts = {}
    nbeaufort_years_with_counts = {}
    sbeaufort_years_with_counts = {}
    other_years_with_counts = {}
    lancaster_t = []
    nbeaufort_t = []
    sbeaufort_t = []
    other_t = []
    years = []
    left_axis = []
    bottom_axis = []
    
    # create subseries for popns
    for t in trophies:
        for k,v in t.iteritems():
            if k == 'app_popn':
                if v == 'Lancaster Sound':
                    lancaster_t.append(t)
                elif v == 'Northern Beaufort Sea':
                    nbeaufort_t.append(t)
                elif v == 'Southern Beaufort Sea':
                    sbeaufort_t.append(t)
                else:
                    other_t.append(t)
                break
     
    # get yearly counts
    years_with_counts = {}
    for t in lancaster_t:
        for k,v in t.iteritems():
            if k =='app_date':
                try: 
                    lancaster_years_with_counts[v.year] += 1 
                except KeyError:
                    lancaster_years_with_counts[v.year] = 1
                try:
                    maxyear = max(v.year, maxyear)
                    minyear = min(v.year, minyear)
                except:
                    minyear = v.year
                    maxyear = v.year
                        
    # get yearly counts
    years_with_counts = {}
    for t in sbeaufort_t:
        for k,v in t.iteritems():
            if k =='app_date':
                try: 
                    sbeaufort_years_with_counts[v.year] += 1 
                except KeyError:
                    sbeaufort_years_with_counts[v.year] = 1
                try:
                    maxyear = max(v.year, maxyear)
                    minyear = min(v.year, minyear)
                except:
                    minyear = v.year
                    maxyear = v.year
           
    # get yearly counts
    years_with_counts = {}
    for t in nbeaufort_t:
        for k,v in t.iteritems():
            if k =='app_date':
                try: 
                    nbeaufort_years_with_counts[v.year] += 1 
                except KeyError:
                    nbeaufort_years_with_counts[v.year] = 1
                try:
                    maxyear = max(v.year, maxyear)
                    minyear = min(v.year, minyear)
                except:
                    minyear = v.year
                    maxyear = v.year
         
    # get yearly counts
    years_with_counts = {}
    for t in other_t:
        for k,v in t.iteritems():
            if k =='app_date':
                try: 
                    other_years_with_counts[v.year] += 1 
                except KeyError:
                    other_years_with_counts[v.year] = 1
                try:
                    maxyear = max(v.year, maxyear)
                    minyear = min(v.year, minyear)
                except:
                    minyear = v.year
                    maxyear = v.year
                       
    # assemble year counts in ordered series
    for y in range(minyear, maxyear + 1):
        try:
            lancaster_counts.append(lancaster_years_with_counts[y])
        except:
            lancaster_counts.append(0)
        try:
            other_counts.append(other_years_with_counts[y])
        except:
            other_counts.append(0)
        try:
            nbeaufort_counts.append(nbeaufort_years_with_counts[y])
        except:
            nbeaufort_counts.append(0)       
        try:
            sbeaufort_counts.append(sbeaufort_years_with_counts[y])
        except:
            sbeaufort_counts.append(0)
    
    # set up chart url
    for y in range(minyear, maxyear + 1):
        bottom_axis.append(y)
    max_count = max(max(sbeaufort_counts), max(nbeaufort_counts), max(other_counts), max(lancaster_counts))
    left_axis = range(0, max_count, 10)
    chart = SimpleLineChart(600, 250, y_range=[0, max_count])
    chart.set_colours(['FFFF00', 'FF0000', '00FF00', '0000FF'])
    chart.set_legend(['Lancaster Sound', 'Northern Beaufort Sea', 'Southern Beaufort Sea', 'Other'])
    chart.set_axis_labels(Axis.LEFT, left_axis)
    chart.set_axis_labels(Axis.BOTTOM, bottom_axis)
    chart.add_data(lancaster_counts)
    chart.add_data(nbeaufort_counts)
    chart.add_data(sbeaufort_counts)
    chart.add_data(other_counts)    
    chart_url = chart.get_url()
     
    return chart_url


# ---------------------------------------------------------------
#    generate bar chart of records/agency
#    (this does not generate interesting information for polar bears)
# ---------------------------------------------------------------
def generate_bar_chart_by_agency_from_local():
    
    # initialize lists
    agency_names = []
    counts = []
    colours = []
    combined = []
    i = 0
            
    # get data 
    for a in Agency.objects.all():
        qset = FedRegDoc.objects.filter(agencies__name=a.name)
        if a.name:
            agency_names.append(a.name)
            counts.append(qset.count())
        elif a.raw_name:
            agency_names.append(a.raw_name)
            counts.append(qset.count())

    # the following section is a hack to order the chart properly
    len_counts = len(counts)
    while i < len_counts:
        combined.append((agency_names[i], counts[i]))
        i += 1
    i=0
    combined = sorted(combined, key=lambda c: c[1], reverse=True)
    print "combined", combined
    counts = []
    agency_names = []
    while i < len_counts:
        counts.append(combined[i][1])
        agency_names.append(combined[i][0])
        i += 1
    agency_names.reverse()
    
    # set up chart
    chart = StackedHorizontalBarChart(600, 400, y_range=[0, max(counts)+10])
    chart.set_colours(['0000FF'])
    chart.set_axis_labels(Axis.LEFT, agency_names)
    chart.add_data(counts)
    chart.set_bar_width(10)
    chart_url = chart.get_url()
    print "chart_url by agency", chart_url
    
    return chart_url
    
#------------------------------------------------------------------------------------------------------------
#    helper for trophy_view - generates map url with markers
#    would work except that it generates a map that is too big for Google Static Map API (too many markers)
#
#------------------------------------------------------------------------------------------------------------
def generate_google_map_with_markers_url(trophies):
    base_map_url = 'http://maps.googleapis.com/maps/api/staticmap'
    map_size = "size=500x400"
    sensor = "sensor=false"
    marker_style = 'size:tiny|color:blue'
    marker_locations = ''
    for t in trophies:
        marker_locations += str(t['lat']) + "," + str(t['lng']) + "|"        
    markers = 'markers=' + marker_style + "|" + marker_locations[:-1] # strips last pipe char
    map_params = map_size + "&" + markers + "&" + sensor
    map_url = base_map_url + "?" + quote(map_params, '&')

    return map_url

