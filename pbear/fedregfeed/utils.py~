from django.contrib.syndication.views import Feed
from fedregfeed.models import FedRegDoc, Agency

from urllib2 import urlopen, quote
import json
import datetime
from math import log10, pow
from pygooglechart import Chart, Axis, SimpleLineChart, StackedHorizontalBarChart
import calendar
import random


# --------------------------------------------------------------
# generate chart url - getting counts from FR api
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
# generate chart url - getting counts from FR api
# -------------------------------------------------------------------------
def generate_chart_url_from_fedreg(search_term, start_year, end_year):
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
        search_result = fetch_page(url) # request page
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
# generate chart url - getting counts from local database
# -------------------------------------------------------------------------
def generate_chart_url_from_local(search_term, start_year, end_year, month_flag):
    ''' returns url for chart after querying local database '''
    
    year_range=range(start_year,end_year + 1)
    month_range=range(1, 13)
    count_rules = []
    count_proprules = []
    count_notices = []
    count_presdocs = []
    count_unknown = []
    today = datetime.date.today()    
        
    for y in year_range:
        if month_flag:
            for m in month_range:
                first_day, last_day = calendar.monthrange(y, m)
                start_date = datetime.date(y, m, 1)
                end_date = datetime.date(y, m, last_day)
                print "start end", start_date, end_date
                month_qset = FedRegDoc.objects.filter(publication_date__range=(start_date, end_date))
                count.append(month_qset.count())
                if end_date > today:
                    break
        else:
            start_date=datetime.date(y,1,1)
            end_date=datetime.date(y,12,31)
            year_qset= FedRegDoc.objects.filter(publication_date__range=(start_date, end_date))       
            count_rules.append(year_qset.filter(document_type='Rule').count())
            count_proprules.append(year_qset.filter(document_type='Proposed Rule').count())
            count_notices.append(year_qset.filter(document_type='Notice').count())
            count_presdocs.append(year_qset.filter(document_type='Presidential Document').count())
            count_unknown.append(year_qset.filter(document_type='Document of Unknown Type').count())

    # set up chart to display
    largest_y = max(max(count_rules), max(count_proprules), max(count_notices), max(count_presdocs), max(count_unknown))
    if largest_y < 100:
        left_axis_step = 10
        max_y = 100
    else:
        left_axis_step = int(pow(10, int(log10(largest_y))) / 10) 
        max_y = (int(largest_y / left_axis_step) * left_axis_step) + (left_axis_step * 2)
    print "left", left_axis_step, "max_y", max_y
    print "max_y", max_y
    left_axis = range(0, max_y + left_axis_step, left_axis_step)
    left_axis[0] = ""
    if month_flag:
        bottom_axis = year_range * 12 # need to fix to account for months
    else:
        bottom_axis = year_range
    chart = SimpleLineChart(600, 300, y_range=[0, max_y])
    chart.set_axis_labels(Axis.LEFT, left_axis)
    chart.set_axis_labels(Axis.BOTTOM, bottom_axis)
    chart.set_grid(0, max(10, int(left_axis_step / 10)), 5, 5)
    chart.set_colours(['0000FF', '00FF00', 'FF0000', 'FFFF00', '00FFFF'])
    chart.set_legend(['Rules', 'Proposed Rules', 'Notices', 'Presidential Docs', 'Unknown'])
    chart.add_data(count_rules)
    chart.add_data(count_proprules)
    chart.add_data(count_notices)
    chart.add_data(count_presdocs)
    chart.add_data(count_unknown)
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

# -----------------------------------------------------------      
#      for the RSS feed
# -----------------------------------------------------------      
class LatestPolarBearUpdate(Feed):
    title="Polar Bear Feed"
    link="/feed/"
    description="Latest notices, rules, and proposed rules from the U.S. Federal Register featuring polar bears." 
    
    def items(self):
        return FedRegDoc.objects.order_by('-publication_date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.abstract
        
    def item_link(self, item):
        return item.html_url
        
    def item_pubdate(self, item):
        return datetime.datetime.combine(item.publication_date, datetime.time())
        
    def item_categories(self, item):
        return item.document_type
        
  
# -----------------------------------------------------------      
#      gets a page of results from the federal register api
#      
# -----------------------------------------------------------
def fetch_page(url):
    '''Retrieves page of FedReg data'''

    # open the url
    try:
        fedregsource = urlopen(url)
    except IOError:
        print "couldn't open URL in fetch_page"
        return False

    # read, close file, and deserialize json data
    jsondata = fedregsource.read()
    fedregsource.close()
    page = json.loads(jsondata)

    return page

# -----------------------------------------------------------      
#     add obj to database
# -----------------------------------------------------------        
def add_object_to_database(d):
    try:
        obj = FedRegDoc(title=d['title'], document_type=d['type'], document_number=d['document_number'], publication_date=d['publication_date'], abstract=d['abstract'], excerpts=d['excerpts'], json_url= d['json_url'], pdf_url=d['pdf_url'], html_url=d['html_url'])    
    except KeyError:
        print "unrecognized key value in add_object_to_database"
        return False    
        
    # if a doc with this doc_number doesn't already exist in database, then add it, html_full_text, and agencies (if the agencies are new)
    if not FedRegDoc.objects.filter(document_number=obj.document_number):
        # get full text as html
        f = urlopen(obj.html_url)
        if f:
            obj.html_full_text = f.read()
        else:
            print "unable to open html url -", obj.html_url, "- in add_object_to_database"
        f.close()
            
        # save object locally
        obj.save()

        # check to see if agencies are new, and if so, save to database
        for a in d['agencies']:
            # extract info from results and put in temporary Agency object
            print "a:" , a
            agency_to_add = Agency()
            for k,v in a.iteritems():
                if k=='url':
                    agency_to_add.url=v
                elif k=='json_url':
                    agency_to_add.json_url=v
                elif k=='raw_name':
                    agency_to_add.raw_name=v
                elif k=='name':
                    agency_to_add.name=v
                elif k=='id':
                    agency_to_add.agency_original_id=v
                else:
                    print "invalid key for agency in add_object_to_database"

            # if new agency id isn't given, or if it's given and doesn't match existing database Agency record, then add it to database
            if not agency_to_add.agency_original_id:
                print "no agency id given, adding to database"
                agency_to_add.save()
            else:
                try:
                    agency_to_add=Agency.objects.get(agency_original_id=agency_to_add.agency_original_id)
                except Agency.DoesNotExist:
                    print "no matching agency in database, adding new" 
                    agency_to_add.save() 
                except Agency.MultipleObjectsReturned:
                    print "multiple matching agency ids in database, selecting the first"
                    agency_to_add=Agency.objects.filter(agency_original_id=agency_to_add.agency_original_id)[0]
            obj.agencies.add(agency_to_add)  
                                  
    return True
                
# -------------------------------------------------------------------
#     updates the database with latest results from federal register
# -------------------------------------------------------------------
def update_database_from_fedreg(base_url, conditions):
    url = base_url + '?' + quote(conditions, safe='/:+=?&"|')
               
    while url:
        search_result_page = fetch_page(url)
        if search_result_page:
            try:
                if search_result_page['errors']:
                    search_result_page = None # this should be changed to actually handle the error
                    print "search errors"
                    break                
            except KeyError:
                try:
                    url = search_result_page['next_page_url']
                except KeyError:
                    url = None
                
                if search_result_page and (search_result_page['count'] is not 0):
                    for d in search_result_page['results']:
                        add_object_to_database(d)
        else:
            break

    return search_result_page

# -------------------------------------------------------------------------------------
#   if recognized state abbrev, expands to full,
#   otherwise returns it as it is except stripped of trailing and leading whitespace
# -------------------------------------------------------------------------------------
def retrieve_full_state_name(state):
    
    state_dict = {
        "AL": 'Alabama', 
        "AK": 'Alaska', 
        "AZ": 'Arizona', 
        "AR": 'Arkansas', 
        "CA": 'California',
        "CO": 'Colorado',
        "CT": 'Connecticut', 
        "DC": 'District of Columbia',
        "DE": 'Delaware', 
        "FL": 'Florida', 
        "GA": 'Georgia',
        "HI": 'Hawaii', 
        "ID": 'Idaho', 
        "IL": 'Illinois', 
        "IN": 'Indiana', 
        "IA": 'Iowa', 
        "KS": 'Kansas', 
        "KY": 'Kentucky', 
        "LA": 'Louisiana', 
        "ME": 'Maine', 
        "MD": 'Maryland',
        "MA": 'Massachusetts', 
        "MI": 'Michigan', 
        "MN": 'Minnesota', 
        "MS": 'Mississippi', 
        "MO": 'Missouri', 
        "MT": 'Montana', 
        "NE": 'Nebraska',
        "NV": 'Nevada', 
        "NH": 'New Hampshire', 
        "NJ": 'New Jersey',
        "NM": 'New Mexico', 
        "NY": 'New York', 
        "NC": 'North Carolina', 
        "ND": 'North Dakota', 
        "OH": 'Ohio', 
        "OK": 'Oklahoma', 
        "OR": 'Oregon',
        "PA": 'Pennsylvania', 
        "RI": 'Rhode Island', 
        "SC": 'South Carolina',
        "SD": 'South Dakota', 
        "TN": 'Tennessee', 
        "TX": 'Texas', 
        "UT": 'Utah', 
        "VT": 'Vermont', 
        "VA": 'Virginia', 
        "WA": 'Washington', 
        "WV": 'West Virginia', 
        "WI": 'Wisconsin', 
        "WY": 'Wyoming',
        "PR": "Puerto Rico"
    }
    
    state = state.strip()
    state = state_dict.get(state, state)
     
    return state


# -------------------------------------------------------------------------------------
#   if recognized state abbrev, expands to full,
#   otherwise returns it as it is except stripped of trailing and leading whitespace
# -------------------------------------------------------------------------------------
def retrieve_abbrev_state_name(state):
    
    state_dict = {
        "AL":'Alabama', 
        "AK":'Alaska', 
         "AZ": 'Arizona', 
        "AR": 'Arkansas', 
        "CA": 'California',
        "CO": 'Colorado',
        "CT": 'Connecticut', 
        "DC": 'District of Columbia',
        "DE": 'Delaware', 
        "FL": 'Florida', 
        "GA": 'Georgia',
        "HI": 'Hawaii', 
        "ID": 'Idaho', 
        "IL": 'Illinois', 
        "IN": 'Indiana', 
        "IA": 'Iowa', 
        "KS": 'Kansas', 
        "KY": 'Kentucky', 
        "LA": 'Louisiana', 
        "ME": 'Maine', 
        "MD": 'Maryland',
        "MA": 'Massachusetts', 
        "MI": 'Michigan', 
        "MN": 'Minnesota', 
        "MS": 'Mississippi', 
        "MO": 'Missouri', 
        "MT": 'Montana', 
        "NE": 'Nebraska',
        "NV": 'Nevada', 
        "NH": 'New Hampshire', 
        "NJ": 'New Jersey',
        "NM": 'New Mexico', 
        "NY": 'New York', 
        "NC": 'North Carolina', 
        "ND": 'North Dakota', 
        "OH": 'Ohio', 
        "OK": 'Oklahoma', 
        "OR": 'Oregon',
        "PA": 'Pennsylvania', 
        "RI": 'Rhode Island', 
        "SC": 'South Carolina',
        "SD": 'South Dakota', 
        "TN": 'Tennessee', 
        "TX": 'Texas', 
        "UT": 'Utah', 
        "VT": 'Vermont', 
        "VA": 'Virginia', 
        "WA": 'Washington', 
        "WV": 'West Virginia', 
        "WI": 'Wisconsin', 
        "WY": 'Wyoming',
        "PR": "Puerto Rico"
    }
    
    new_state = None
    state = state.strip()
    for abbrev,full in state_dict.iteritems():
        if state == full:
            new_state = abbrev
            break
        elif state == abbrev:
            new_state = abbrev
            break

    print state, new_state
 
    if new_state:
        return new_state
    else:
        return None

