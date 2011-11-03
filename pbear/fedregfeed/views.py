from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core import serializers
from django.http import Http404
from django.template import RequestContext

from urllib2 import urlopen, quote
import re
import json
import datetime
from operator import itemgetter

from fedregfeed.models import FedRegDoc, Agency
from utils import update_database_from_fedreg, generate_chart_url_from_fedreg, generate_chart_url_from_local, generate_bar_chart_by_agency_from_local, generate_trophy_map_chart_url, retrieve_full_state_name, retrieve_abbrev_state_name

# --------------------------------------------------------------------------------------------------------------
# the multiple view shows a list of records in the database
# --------------------------------------------------------------------------------------------------------------
def multiple(request, **kwargs):

    # check for search arg
    try:
        search_term = kwargs['search_term']
    except KeyError:
        search_term = None
        print "no 'search_term' arg passed to multiple view"

    # check for update arg
    try:
        update_database_flag = kwargs['update_database_flag']
        print "update_database_flag value:", update_database_flag
    except KeyError:
        update_database_flag = False
        print "no update_database_flag passed to multiple view"    

    # there should always be a display_num parameter (i.e., number of items to display per page)    
    try:
        display_num=int(kwargs['display_num'])
        print "display_num", display_num
    except KeyError:
        raise Http404

    # update the database if flag is set
    # if database contains docs already, then only search for more recent items than contained in database (ie., add a "gte" condition)
    if update_database_flag:
        print "updating database"
        fr_base_url = 'http://api.federalregister.gov/v1/articles.json'
        fr_conditions = 'conditions[term]=\"polar bear\"|\"polar bears\"'         
        try:
            most_recent_doc_pub_date = FedRegDoc.objects.all().order_by('-publication_date')[0].publication_date
            fr_conditions = fr_conditions + '&' + 'conditions[publication_date][gte]=' + most_recent_doc_pub_date.strftime("%m/%d/%Y")  
        except IndexError:
            print "no records found in database in multiple, starting from scratch"
            pass
        request_return = update_database_from_fedreg(fr_base_url, fr_conditions)

    print "getting matching list of docs to search term (or all)"
    # get list of  docs matching search term, if there is a search term; otherwise get all
    if search_term:
        doc_list = FedRegDoc.objects.filter(html_full_text__contains=search_term)
    else:
        doc_list = FedRegDoc.objects.all()

    # either get the requested doc_pk as first item to show ....  
    try:
        print "trying to get doc_pk object"
        doc_pk=int(kwargs['doc_pk'])
        # need to add check here for whether doc_pk is in search result set
        doc_list = doc_list.order_by('-publication_date') # formerly had a list conversion here, not sure if necessary
        total_doc_count = doc_list.count()
        # got to be more efficient way to do the following! (i.e., find position of doc_pk object in date-ordered list)
        for display_offset in range(total_doc_count):
            if doc_list[display_offset].pk == doc_pk:
                break
    # ...  or if no doc_pk given, show the most recent item
    except KeyError:
        print "no doc_pk, instead retrieving most recent"
        # get the pk of the newest item by pub date
        doc_list = doc_list.order_by('-publication_date')
        doc_pk = doc_list[0].pk
        display_offset = 0
        total_doc_count = FedRegDoc.objects.count()        

    print "total_doc_count", total_doc_count
    print "setting nav parameters"
    # set nav parameters
    try:
        if display_offset == 0:
            newest_pk=None
            newer_pk= None
        else:
            newest_pk = doc_list[0].pk
            newer_pk = doc_list[max(0, display_offset - display_num)].pk
    except IndexError:
        print "keyerror setting newest/er"
        raise Http404

    try:
        if (display_offset + display_num) >= total_doc_count:
            display_num = total_doc_count - display_offset + 1
            older_pk = None
            oldest_pk = None
        else:    
            older_pk = doc_list[min(total_doc_count - 1, display_offset + display_num)].pk
            oldest_pk = doc_list[max(0, total_doc_count - display_num)].pk
    except IndexError:
        print "keyerror setting oldest/er"
        raise Http404

    print "truncating list"
    # truncate doc_list to subset to display on this page   
    doc_list=doc_list[display_offset:(display_offset + display_num)]

                
    print "rendering"
    # render html via template
    return render_to_response('multiple.html', {"doc_list":doc_list, 'search_term':search_term, "doc_pk":doc_pk, "display_offset": display_offset, "display_num":display_num, "newest_pk":newest_pk, "newer_pk":newer_pk, "older_pk":older_pk, "oldest_pk":oldest_pk, "total_doc_count":total_doc_count}, context_instance=RequestContext(request))


# --------------------------------------------------------------------------------------------------------------
# the single view shows details for a single fedreg document based on primary key (pk) number
# --------------------------------------------------------------------------------------------------------------
def single(request, **kwargs):

    # set defaults
    comment_posted = False
    doc_pk = None

    # get arguments from kwargs
    for k,v in kwargs.iteritems():
        if k == 'comment':
            comment_posted = v
        elif k == 'doc_pk':
            doc_pk = int(v)
        else:
            print "invalid argument - ", k, " - passed to single"
            raise Http404

    # get doc from database 
    try: 
        if not doc_pk:
            print "no doc_pk given to single view - showing first by publication date"
            doc = FedRegDoc.objects.order_by('-publication_date')[0]
        else:
            doc = FedRegDoc.objects.get(pk=doc_pk)
    except FedRegDoc.DoesNotExist:
        raise Http404

    # find primary key for nav to newer/newest record
    newest_pk = FedRegDoc.objects.order_by('-publication_date')[0].pk
    if newest_pk == doc.pk:
        newest_pk = None
        newer_pk = None
    else:
        q = list(FedRegDoc.objects.order_by('publication_date').filter(publication_date__gte = doc.publication_date).distinct())
        i = 0
        for i in range(len(q)):
            if q[i].pk == doc.pk:
                break
        try:
            newer_pk = q[i+1].pk
        except IndexError:
            newer_pk = None
            newest_pk = None

    # find primary key for nav to older/oldest record
    oldest_pk = FedRegDoc.objects.order_by('publication_date')[0].pk
    if oldest_pk == doc.pk:
        oldest_pk = None
        older_pk = None
    else:
        q = list(FedRegDoc.objects.order_by('-publication_date').filter(publication_date__lte=doc.publication_date).distinct())
        i = 0
        for i in range(len(q)):
            if q[i].pk == doc.pk:
                break
        try:
            older_pk = q[i+1].pk
        except IndexError:
            older_pk = None
            oldest_pk = None
        
    # render page
    return render_to_response('single.html', {"doc":doc, "comment_posted":comment_posted, "newer_pk":newer_pk, "older_pk":older_pk, "newest_pk":newest_pk, "oldest_pk":oldest_pk}, context_instance=RequestContext(request))


#-----------------------------------------------------------
#   pbear chart
#-------------------------------------------------------------
def pbear_chart(request, **kwargs):

    for k,v in kwargs.iteritems():  
        print k, v
        if k=='search_term':
            search_term = v
        elif k=='end_year':
            end_year = int(v)
        elif k=='start_year': 
            start_year = int(v)
        else:
            print "invalid argument - ", k, " - passed to pbear_chart"
            raise Http404

    month_flag = False
    # the following generates chart from local database
    chart_url = generate_chart_url_from_local(search_term, start_year, end_year, month_flag)  
    # the following generates chart from FR API
    # chart_url = generate_chart_url_from_fedreg(search_term, start_year, end_year)

    # the following line generates a bar chart showing number of records per agency 
    # bar_chart_url = generate_bar_chart_by_agency_from_local()
    bar_chart_url = None
     
    return render_to_response('chart.html', {"chart_url": chart_url, "bar_chart_url":bar_chart_url, "search_term":search_term, "end_year":end_year, "start_year":start_year}, context_instance=RequestContext(request))


# ------------------------------------------------
#    add html_full_text to database
#     (only if missing from record) 
#
#    this is meant to be a run-once function
#    to avoid reloading entire database
# ------------------------------------------------
def add_html_full_text_to_all(request):
    for d in FedRegDoc.objects.all():
        print d.title
        if not d.html_full_text:
            try:
                f=urlopen(d.html_url)
                d.html_full_text=f.read()
                f.close()
                d.save()
            except URLError:
                print "URLError when opening ", d.html_url
                
    return render_to_response('add_html_full_text.html', {}, context_instance=RequestContext(request))


# ---------------------------------------------------
#        clean up full text html so it's easier to 
#        extract data from
#
#   a helper for show_trophy
# ---------------------------------------------------
def strip_polar_bear_html(html_full_text):
    full_text_stripped = re.sub(r"<.*?>", " ", html_full_text)
    full_text_stripped = re.sub(r"\s+", " ", full_text_stripped)
    full_text_stripped = re.sub(r"Back to Top", " ", full_text_stripped)
    full_text_stripped = re.sub(r"Lancaster Sound polar bear from the Lancaster Sound", "Lancaster Sound", full_text_stripped)

    return full_text_stripped        

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
    
#------------------------------------------------------------------------------------------------------------
#    helper for show_trophy - generates map url
#    would work except that it generates a map that is too big for Google Static Map API (too many markers)
#
#    (possibly could work if generated KML?)
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

        
# --------------------------------------------
#    trophy map and detail view
#---------------------------------------------
def show_trophy(request, **kwargs):
            
    google_geocode_flag = False # NEED TO SET TO True TO ALLOW GEOCODING    

    trophies = []
    trophies_sorted=[]
    state_counts = {}
    state_counts_sorted = []
    state_counts_total = 0
    
    # find all records that contain permit apps for trophy import
    qset = FedRegDoc.objects.filter(html_full_text__contains="applicant requests a permit to import a polar bear")
    qset = qset.filter(html_full_text__contains="sport")
    #print "count", qset.count()
            
    # set up regex to extract trophy data from full html text (still problems with some false negs)
    trophy_search_re = re.compile(r"Applicant:[ ]+(?P<app_name_prefix>Dr\.)?([ ]+)?(?P<app_name>[\w\s.-]+),?(\s+)?(?P<app_name_suffix>III|IV|MD|Jr(\.)?|Sr(\.)?|Inc(\.)?)?,?[ ]+(?P<app_city>[ \w\.-]+),[ ]+(?P<app_state>\w\w)(,?[ ]+(?P<app_num>[-,\w\s]+))?(\.)?(\s+)?The applicant requests a permit to import a polar bear(.+?)from the[ ]+(?P<app_popn>[ \w]+)[ ]+polar bear population",re.DOTALL)
         
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
            app_state = retrieve_abbrev_state_name(t.group('app_state')) 
            # following section makes sure permit number isn't just whitespace
            app_num = t.group('app_num')
            if app_num:
                if t.group('app_num').strip() == '':
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

    # sum number of permit apps per state
    for t in trophies:
        for k,v in t.iteritems():
            if k == 'app_state':
                if v != None:
                    if state_counts.get(v):
                        state_counts[v] += 1
                    else:
                        state_counts[v] = 1

    # create sorted lists of (full) state names and counts for better display
    for k,v in state_counts.iteritems():
        state_counts_sorted.append([retrieve_full_state_name(k), v])
        state_counts_total += int(v)
    state_counts_sorted.sort(key=itemgetter(0))    

    # sort trophy details by date for display and place in list of lists
    for t in trophies:
        trophies_sorted.append([t['app_date'], t['app_name_prefix'], t['app_name'], t['app_name_suffix'], t['app_city'], t['app_state'], t['app_num'], t['app_popn']]) # if using lat/lng would need to add in here
    trophies_sorted.sort(key=itemgetter(0))         
    
    # generate URL to map state counts using Google Map Chart 
    map_url = generate_trophy_map_chart_url(state_counts)
        
    return render_to_response('trophy.html', {"trophies_sorted":trophies_sorted, "state_counts_sorted":state_counts_sorted, "state_counts_total":state_counts_total, 'map_url':map_url}, context_instance=RequestContext(request))


#-----------------------------------------------------------
#      polar bear search
#      should return a list of matching primary keys to FedRegDocs
#-----------------------------------------------------------
def polar_bear_search(search_string):

    matching_docs = []
    
    search_re = re.compile(r'.*' + search_string + ".*", re.DOTALL)

    for d in FedRegDoc.objects.all():
        if search_re(d.html_full_text):
            matching_docs.append(d.pk)

    return matching_docs
    

