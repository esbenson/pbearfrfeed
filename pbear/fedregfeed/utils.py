from django.contrib.syndication.views import Feed
from fedregfeed.models import FedRegDoc, Agency

from urllib2 import urlopen, quote
import json
import datetime
import re

#------------------------------
# regularize popn names for trophy view
#------------------------
def regularize_population_name(popn):
    if popn == None:
        return None

    if popn == 'South Beaufort Sea':
        popn = 'Southern Beaufort Sea'
    if popn == 'South Beaufort Sea':
        popn = 'Southern Beaufort Sea'
    if popn == 'Southern Beaufort':
        popn = 'Southern Beaufort Sea'
    if popn == 'Southern Beauford':
        popn = 'Southern Beaufort Sea'
    if popn == 'Southern Beauford Sea':
        popn = 'Southern Beaufort Sea'
    if popn == 'Southern Beauford sea':
        popn = 'Southern Beaufort Sea'
    if popn == 'Southern Beaufort sea':
        popn = 'Southern Beaufort Sea'
    if popn == 'Southern Beafort Sea':
        popn = 'Southern Beaufort Sea'
    if popn == 'northern Beaufort':
        popn = 'Northern Beaufort Sea'
    if popn == 'northern Beaufort':
        popn = 'Northern Beaufort Sea'
    if popn == 'Northern Beaufort':
        popn = 'Northern Beaufort Sea'
    if popn == 'Northern Beaufort sea':
        popn = 'Northern Beaufort Sea'
    if popn == 'Lancaster sound':
        popn = 'Lancaster Sound'
    if popn == 'Landcaster Sound':
        popn = 'Lancaster Sound'
    if popn == 'Lancaster Sound Bay':
        popn = 'Lancaster Sound'
    if popn == 'Viscount Melville':
        popn = 'Viscount Melville Sound'
    if popn == 'Viscount Mellville Sound':
        popn = 'Viscount Melville Sound'
    if popn == 'Davis Straight':
        popn = 'Davis Strait'
    if popn == 'Perry Channel':
        popn = 'Parry Channel'
    if popn == 'Fox Basin':
        popn = 'Foxe Basin'
    if popn == 'Norweigian Bay':
        popn = 'Norwegian Bay'
        
    return popn
        
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
def fetch_fedreg_results_page(url):
    '''Retrieves page of FedReg data'''

    # open the url
    try:
        fedregsource = urlopen(url)
    except:
        print "couldn't open URL in fetch_fedreg_results_page"
        return None

    # read, close file, and deserialize json data
    jsondata = fedregsource.read()
    fedregsource.close()
    print "jsondata:" , jsondata
    if jsondata:
        try:
            page = json.loads(jsondata)
        except ValueError:
            print "unable to load jsondata in fetch_fedreg_results_page"
            return None
    else:
        print "no jsondata retrieved from url source in fetch_fedreg_results_page" 

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
        search_result_page = fetch_fedreg_results_page(url)
        if search_result_page:
            try:
                if search_result_page['errors']:
                    search_result_page = None # this should be changed to actually handle the error
                    print "search errors in update_database"
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
def full_state_name_from_abbrev(state):
    
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
    state = state_dict.get(state, state) # gets value in dict for state; if none, returns current value by default (i.e., leaves unchanged)
     
    return state


# -------------------------------------------------------------------------------------
#   if recognized state abbrev, expands to full,
#   otherwise returns it as it is except stripped of trailing and leading whitespace
# -------------------------------------------------------------------------------------
def abbrev_state_name_from_full(state):
    
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
 
    return new_state

#-----------------------------------------------------------
#      polar bear search
#      should return a list of matching primary keys to FedRegDocs
#-----------------------------------------------------------
def polar_bear_search(search_string):

    matching_docs = []
    
    search_re = re.compile(r'.*' + search_string + r'.*', re.DOTALL)

    for d in FedRegDoc.objects.all():
        if d.html_fulltext:
            if search_re.search(d.html_full_text): 
                print "found match in polar_bear_search for doc.pk:", d.pk  
                matching_docs.append(d.pk)

    return matching_docs
    

# --------------------------------------------
#    helper for trophy view
#   extracts records for database 
# and if flag set, uses google to geocode towns
#---------------------------------------------
def extract_trophy_records_from_local(google_geocode_flag):

    trophies = []
    trophy_dict = {}
    
    # find all records that contain permit apps for trophy import - basically, use a first pass in the database to speed up search
    qset = FedRegDoc.objects.filter(html_full_text__contains="applicant requests a permit to import a polar bear")
    qset = qset.filter(html_full_text__contains="sport")
    #print "count", qset.count()
            
    # set up regex to extract trophy data from full html text (still problems with some false negs  and missing PRTs (permit numbers))
    trophy_search_re = re.compile(r"(?P<app_num_pre>PRT-\w+)?[\s+]?Applicant:[ ]+(?P<app_name_prefix>Dr\.)?([ ]+)?(?P<app_name>[\w\s.-]+),?[ ]*(?P<app_name_suffix>III|IV|MD|Jr(\.)?|Sr(\.)?|Inc(\.)?)?,?[ ]+(?P<app_city>[ \w\.-]+),[ ]+(?P<app_state>\w\w)(,?[ ]+(?P<app_num>[-,\w\s]+))?(\.)?(\s+)?The applicant requests a permit to import a polar bear(.+?)from the[ ]+(?P<app_popn>[ \w]+)[ ]+polar bear population",re.DOTALL)
         
    # get applicant name, city, applicant date, etc. from each matching Fedregdoc
    for d in qset:
        # following strips html tags (roughly), replace all whitespace with spaces, and deal with a couple of specific problems with source material
        # (if data is available as json, this would be a better place to start than the current approach)
        full_text_stripped = strip_polar_bear_html(d.html_full_text)

        # following loops through all the re matches for this document 
        for t in trophy_search_re.finditer(full_text_stripped):
            app_date = d.publication_date    
            app_name = t.group('app_name')
            app_name_suffix = t.group('app_name_suffix')
            app_name_prefix = t.group('app_name_prefix')
            app_city = t.group('app_city')
            app_state = t.group('app_state')
            app_popn=t.group('app_popn')     
            # following line converts written-out name to two-letter abbrevs or "None" if not recognized as valid US state name
            app_state = abbrev_state_name_from_full(t.group('app_state')) 
            # following section makes sure permit number isn't just whitespace
            if t.group('app_num_pre'):
                app_num = t.group('app_num_pre')
            else:
                app_num = t.group('app_num')
            if app_num:
                if app_num.strip() == '':
                    app_num = None

            trophy_dict = {"app_date":app_date, "app_name":app_name, "app_name_suffix":app_name_suffix, "app_name_prefix":app_name_prefix, "app_city":app_city, "app_state":app_state, "app_num":app_num, "app_popn":app_popn, 'lat':None, 'lng':None}

            # geocode lat/long from city/state: the following works (as long as not over google api limit)
            # currently, stops trying to geocode on any error
            if google_geocode_flag:
                geocode_result = google_geocode(app_city + ",+" + app_state)
                if geocode_result:
                    trophy_dict['lat'] = geocode_result['lat']
                    trophy_dict['lng'] = geocode_result['lng']
                else:
                    google_geocode_flag = False
            else:
                trophy_dict['lat'] = trophy_dict['lng'] = None
                
            trophies.append(trophy_dict)

    return trophies
        
        
# --------------------------------------------
#    google geocode helper for show_trophy 
#---------------------------------------------
def google_geocode(address_string):
    geocode_result = {}

    base_geocode_url = "http://maps.googleapis.com/maps/api/geocode/json"
    params =  "address=" + address_string + "&" + "sensor=false"
    geocode_url = base_geocode_url + "?" + quote(params, "+&,=")
    try:
        f = urlopen(geocode_url)
        geocode_result_json = f.read()
        f.close()
        geocode_result = json.loads(geocode_result_json)
        print "geocode_url:", geocode_url
        print "geocode_result:", geocode_result
        if geocode_result['status'] =='OK':            
            try:
                geocode_result['lat']= geocode_result['results'][0]['geometry']['location']['lat']
                geocode_result['lng']= geocode_result['results'][0]['geometry']['location']['lng']
            except KeyError, IndexError:
                geocode_result = False
        elif geocode_result['status'] == 'OVER_QUERY_LIMIT': # if failed because too many queries
            geocode_result = False 
        else:
            geocode_result = False # if failed for any reason
    except URLError:
        print "URLError opening ", geocode_url
        geocode_reult = False
        
    return geocode_result

# ---------------------------------------------------
#        clean up full text html so it's easier to 
#        extract data from
#
#   a helper for show_trophy
# ---------------------------------------------------
def strip_polar_bear_html(html_full_text):
    # these are to roughly strip HTML tags and replace whitespace with a single space
    full_text_stripped = re.sub(r"<.*?>", " ", html_full_text)
    full_text_stripped = re.sub(r"\s+", " ", full_text_stripped)

    # these are to address specific problems with source text with trophies
    full_text_stripped = re.sub(r"Back to Top", " ", full_text_stripped)
    full_text_stripped = re.sub(r"Lancaster Sound polar bear from the Lancaster Sound", "Lancaster Sound", full_text_stripped)
    full_text_stripped = re.sub(r"Northern Beaufort population polar bear population", "Northern Beaufort polar bear population", full_text_stripped)
     
    return full_text_stripped        

