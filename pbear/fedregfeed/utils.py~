from django.contrib.syndication.views import Feed
from fedregfeed.models import FedRegDoc, Agency

from urllib2 import urlopen, quote
import json
import datetime


#------------------------------
# regularize popn names for trophy view
#------------------------
def regularize_population_name(popn):
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

