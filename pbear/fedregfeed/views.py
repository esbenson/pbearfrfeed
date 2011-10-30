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
    
    try:
        display_num=int(kwargs['display_num'])
    except KeyError:
        raise Http404

    try:
       doc_pk=max(0, int(kwargs['doc_pk']))
       doc_list=list(FedRegDoc.objects.all().order_by('-publication_date'))
       # find offset for given doc_pk
       total_doc_count = FedRegDoc.objects.count()
       for display_offset in range(total_doc_count):
           if doc_list[display_offset].pk == doc_pk:
               break
    except KeyError:
        # if no 'doc_pk' was given, then update database and get the most recent by publication date
        base_url = 'http://api.federalregister.gov/v1/articles.json'
        conditions = 'conditions[term]=\"polar bear\"|\"polar bears\"'         
        # if database contains docs already, then only search for more recent items than contained in database (ie., add a "gte" condition)
        try:
            most_recent_doc_pub_date = FedRegDoc.objects.all().order_by('-publication_date')[0].publication_date
            conditions = conditions + '&' + 'conditions[publication_date][gte]=' + most_recent_doc_pub_date.strftime("%m/%d/%Y")  
        except IndexError:
            conditions = conditions
        # update the database 
        request_return = update_database_from_fedreg(base_url, conditions)
        # get the pk of the newest item by pub date
        doc_list = FedRegDoc.objects.order_by('-publication_date')
        doc_pk = doc_list[0].pk
        display_offset = 0
        total_doc_count = FedRegDoc.objects.count()        

    # set nav parameters
    if display_offset == 0:
        newest_pk=None
        newer_pk=None
    else:
        newest_pk = doc_list[0].pk
        newer_pk = doc_list[max(0, display_offset - display_num)].pk
    if (display_offset + display_num) >= total_doc_count:
        display_num = total_doc_count - display_offset + 1
        older_pk = None
        oldest_pk = None
    else:    
        older_pk = doc_list[min(total_doc_count - 1, display_offset + display_num)].pk
        oldest_pk = doc_list[max(0, total_doc_count - display_num)].pk
    
    doc_list=doc_list[display_offset:(display_offset + display_num)]

    # render html via template
    return render_to_response('multiple.html', {"doc_list":doc_list, "doc_pk":doc_pk, "display_offset": display_offset, "display_num":display_num, "newest_pk":newest_pk, "newer_pk":newer_pk, "older_pk":older_pk, "oldest_pk":oldest_pk, "total_doc_count":total_doc_count}, context_instance=RequestContext(request))



# --------------------------------------------------------------------------------------------------------------
# the single view shows details for a single fedreg document based on primary key (pk) number
#
# --------------------------------------------------------------------------------------------------------------
def single(request, **kwargs):

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

#    chart_url = generate_chart_url_from_fedreg(search_term, start_year, end_year) # generate from fedreg API
    month_flag = False
    chart_url = generate_chart_url_from_local(search_term, start_year, end_year, month_flag)  # generate from local database

    # bar_chart_url = generate_bar_chart_by_agency_from_local()
    bar_chart_url = None
     
    return render_to_response('chart.html', {"chart_url": chart_url, "bar_chart_url":bar_chart_url, "search_term":search_term, "end_year":end_year, "start_year":start_year}, context_instance=RequestContext(request))


# ------------------------------------------------
#    add html_full_text to database
#     (only if missing from record) 
# ------------------------------------------------
def add_html_full_text_to_all(request):
    print "in add_html_full_text"
    for d in FedRegDoc.objects.all():
        print d.title
        if not d.html_full_text:
            f=urlopen(d.html_url)
            d.html_full_text=f.read()
            f.close()
            d.save()
        
    return render_to_response('add_html_full_text.html', {}, context_instance=RequestContext(request))


# --------------------------------------------
#    trophy map and detail view
#---------------------------------------------
def show_trophy(request, **kwargs):
    
    trophies = []
    
    # find all records that contain permit apps for trophy import
    qset = FedRegDoc.objects.filter(html_full_text__contains="applicant requests a permit to import a polar bear")
    qset = qset.filter(html_full_text__contains="sport")
    print "count", qset.count()
        
    # set up regex to extract trophy data from full html text (still problems with some false negs)
    trophy_search_re = re.compile(r"Applicant:[ ]+(?P<app_name_prefix>Dr\.)?([ ]+)?(?P<app_name>[\w\s.-]+),?(\s+)?(?P<app_name_suffix>III|IV|MD|Jr(\.)?|Sr(\.)?|Inc(\.)?)?,?[ ]+(?P<app_city>[ \w\.-]+),[ ]+(?P<app_state>\w\w)(,?[ ]+(?P<app_num>[-,\w\s]+))?(\.)?(\s+)?The applicant requests a permit to import a polar bear(.+?)from the[ ]+(?P<app_popn>[ \w]+)[ ]+polar bear population",re.DOTALL)
         
    # get applicant name, city, applicant date, etc. from each matching Fedregdoc
    for d in qset:
        # strip tags (roughly), replace all whitespace with spaces, and deal with a couple of specific problems with source material
        full_text_stripped = re.sub(r"<.*?>", " ", d.html_full_text)
        full_text_stripped = re.sub(r"\s+", " ", full_text_stripped)
        full_text_stripped = re.sub(r"Back to Top", " ", full_text_stripped)
        full_text_stripped = re.sub(r"Lancaster Sound polar bear from the Lancaster Sound", "Lancaster Sound", full_text_stripped)
        
        print d.publication_date         
        
        for t in trophy_search_re.finditer(full_text_stripped):
            app_date = d.publication_date    
            app_name = t.group('app_name')
            app_name_suffix = t.group('app_name_suffix')
            app_name_prefix = t.group('app_name_prefix')
            app_city = t.group('app_city')
            app_state = t.group('app_state')
            app_state = retrieve_abbrev_state_name(t.group('app_state')) # converts to two-letter abbrevs or "None" if not recognized as valid US state name
            if t.group('app_num'):
                if t.group('app_num').strip() == '':
                    app_num = None
                else:
                    app_num = t.group('app_num')
            else:
                app_num = None
            app_popn=t.group('app_popn')     
            trophy_dict = {"app_date":app_date, "app_name":app_name, "app_name_suffix":app_name_suffix, "app_name_prefix":app_name_prefix, "app_city":app_city, "app_state":app_state, "app_num":app_num, "app_popn":app_popn, 'lat':None, 'lng':None}

            print trophy_dict

            # ------ the following works (as long as not over google api limit) --- geocode - lat/long from city/state
            google_geocode_OVER_QUERY_LIMIT = True # NEED TO SET TO FALSE TO ALLOW GEOCODING
            if not google_geocode_OVER_QUERY_LIMIT:
                if app_state:
                    base_geocode_url = "http://maps.googleapis.com/maps/api/geocode/json"
                    params =  "address=" + app_city + ",+" + app_state + "&" + "sensor=false"
                    geocode_url = base_geocode_url + "?" + quote(params, "+&,=")
                    f = urlopen(geocode_url)
                    geocode_result_json = f.read()
                    f.close()
                    geocode_result = json.loads(geocode_result_json)
                    print "geocode_url:", geocode_url
                    print "geocode_result:", geocode_result
                    if geocode_result['status'] =='OK':            
                        trophy_dict['lat'] = geocode_result['results'][0]['geometry']['location']['lat']
                        trophy_dict["lng"] = geocode_result['results'][0]['geometry']['location']['lng']
                    else:
                        trophy_dict['lat'] = trophy_dict['lng'] = 0
                        if geocode_result['status'] == 'OVER_QUERY_LIMIT': # stop hammering the google geocoder if over limit
                            google_geocode_OVER_QUERY_LIMIT = True
             # --- end geocoding
                
            trophies.append(trophy_dict)

    # calculate number of permit apps by state
    state_counts = {}
    for t in trophies:
        for k,v in t.iteritems():
            if k == 'app_state':
                if v != None:
                    if state_counts.get(v):
                        state_counts[v] += 1
                    else:
                        state_counts[v] = 1
    print state_counts

    # create sorted lists of (full) state names and counts for better display
    state_counts_sorted = []
    for k,v in state_counts.iteritems():
        print retrieve_full_state_name(k),v
        state_counts_sorted.append([retrieve_full_state_name(k), v])
    state_counts_sorted.sort(key=itemgetter(0))    
    print "state_counts_sorted\n" , state_counts_sorted
 
    # sort trophy details by date for display
    trophies_sorted=[]
    for t in trophies:
        trophies_sorted.append([t['app_date'], t['app_name_prefix'], t['app_name'],t['app_name_suffix'],t['app_city'],t['app_state'],t['app_num'], t['app_popn']]) # if using lat/lng would need to add in here
    trophies_sorted.sort(key=itemgetter(0))         
    
    #-----the following would work except that it generates a map that is too big for Google Static Map API (too many markers)
    #base_map_url = 'http://maps.googleapis.com/maps/api/staticmap'
    #map_size = "size=500x400"
    #sensor = "sensor=false"
    #marker_style = 'size:tiny|color:blue'
    #marker_locations = ''
    #for t in trophies:
    #    marker_locations += str(t['lat']) + "," + str(t['lng']) + "|"        
    #markers = 'markers=' + marker_style + "|" + marker_locations[:-1] # strips last pipe char
    #map_params = map_size + "&" + markers + "&" + sensor
    #map_url = base_map_url + "?" + quote(map_params, '&')

    # generate URL to map using Google Map Chart 
    map_url = generate_trophy_map_chart_url(state_counts)
        
    return render_to_response('trophy.html', {"trophies_sorted":trophies_sorted, 'map_url':map_url, "state_counts_sorted":state_counts_sorted}, context_instance=RequestContext(request))


