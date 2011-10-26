from django.contrib.syndication.views import Feed

from urllib2 import urlopen, quote
import json
from datetime import datetime, time
from math import log10, pow
from pygooglechart import Chart, Axis, SimpleLineChart

from fedregfeed.models import FedRegDoc, Agency


#--------------------------------------------------------------
# generate chart url
#-------------------------------------------------------------------------
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



# -----------------------------------------------------------      
#      for the RSS feed
# -----------------------------------------------------------      
class LatestPolarBearUpdate(Feed):
    title="Polar Bear FedReg Feed"
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
        return datetime.combine(item.publication_date, time())
        
    def item_categories(self, item):
        return item.document_type
        
  
# -----------------------------------------------------------      
#      gets a page of results from the federal register api
#      (with no error checking)
# -----------------------------------------------------------
def fetch_page(url):
    '''Retrieves page of FedReg data'''
    
    fedregsource = urlopen(url)
    jsondata = fedregsource.read()
    fedregsource.close()
    page = json.loads(jsondata)
        
    return page


# -----------------------------------------------------------      
#     add obj to database
# -----------------------------------------------------------      
def add_object_to_database(d):
    obj = FedRegDoc(title=d['title'], document_type=d['type'], document_number=d['document_number'], publication_date=d['publication_date'], abstract=d['abstract'], excerpts=d['excerpts'], json_url= d['json_url'], pdf_url=d['pdf_url'], html_url=d['html_url'])    

    # if a doc with this doc_number doesn't already exist in database, then add it and its agencies (if the agencies are new)
    if not FedRegDoc.objects.filter(document_number=obj.document_number):
        obj.save()
    
        # check to see if agencies are new, and if so, save to database
        for a in d['agencies']:
            # extract info from results and put in temporary Agency object
            agency_to_add = Agency()
            try:
                agency_to_add.url=a['url']
            except KeyError:
                agency_to_add.url=None
        
            try:
                agency_to_add.json_url=a['json_url']
            except KeyError:
                agency_to_add.json_url=None
        
            try: 
                agency_to_add.raw_name=a['raw_name']
            except KeyError:
                agency_to_add.raw_name=None
            
            try:
                agency_to_add.name=a['name']
            except KeyError:
                agency_to_add.name=None
        
            try:
                agency_to_add.agency_original_id=a['id']
            except KeyError:
                agency_to_add.agency_original_id=None

            # if new agency id isn't given, or if it's given and doesn't match existing database Agency record, then add it to database
            if agency_to_add.agency_original_id is None:
                print "no agency id given, adding to database"
                agency_to_add.save()
            else:
                try:
                    agency_to_add=Agency.objects.get(agency_original_id=agency_to_add.agency_original_id)
                except Agency.DoesNotExist:
                    print "no matching agency in database, adding new" 
                    agency_to_add.save() 
                except Agency.MultipleObjectsReturned:
                    print "multiple matching agency objects in database, selecting the first"
                    agency_to_add=Agency.objects.filter(agency_original_id=agency_to_add.agency_original_id)[0]
            obj.agencies.add(agency_to_add)                        
    # return to beginning of for loop through docs in results 
                
                
# --------------------------------------------------------------
#     updates the database with latest results 
# --------------------------------------------------------------
def update_database_from_fedreg(base_url, conditions):
    url = base_url + '?' + quote(conditions, safe='/:+=?&"|')
               
    while url is not None:
        search_result_page = fetch_page(url)
        try:
            if search_result_page['errors']:
                search_result_page = None # this should be changed to actually handle the error
                break                
        except KeyError:
            try:
                url = search_result_page['next_page_url']
            except KeyError:
                url = None
            
            if search_result_page and (search_result_page is not 0):
                for d in search_result_page['results']:
                    add_object_to_database(d)

    return search_result_page
