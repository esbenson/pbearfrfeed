from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.http import Http404
from django.template import RequestContext

from urllib2 import urlopen, quote
import re, json, datetime
from operator import itemgetter

from fedregfeed.models import FedRegDoc
from utils import update_database_from_fedreg, full_state_name_from_abbrev, abbrev_state_name_from_full, regularize_population_name, extract_trophy_records_from_local, google_geocode
from charts import generate_freq_chart_url_from_fedreg, generate_freq_chart_url_from_qset, generate_bar_chart_by_agency_from_local, generate_trophy_map_chart_url, generate_pie_chart_source_popn, generate_trophy_freq_chart_url


#-----------------------------------------------------------
#   home
#
#   generates chart URL from local database to include
#  in front page
# and updates database if flag is set
# 
#-------------------------------------------------------------
def home_view(request, **kwargs):
    print "in home"

    # check for args
    try:
        update_database_flag = kwargs['update_database_flag']
    except KeyError:
        update_database_flag = False
        
    try:
        search_term = kwargs['search_term']
    except KeyError:
        search_term = None
        print "no 'search_term' arg passed to multiple view"
        raise Http404

    # update the database if flag is set
    # if database contains docs already, then only search for more recent items than contained in database (ie., add a "gte" condition)
    if update_database_flag:
        print "updating database"
        fr_base_url = 'http://api.federalregister.gov/v1/articles.json'
        fr_conditions = 'conditions[term]=' + search_term         
        try:
            most_recent_doc_pub_date = FedRegDoc.objects.all().order_by('-publication_date')[0].publication_date
            fr_conditions = fr_conditions + '&' + 'conditions[publication_date][gte]=' + most_recent_doc_pub_date.strftime("%m/%d/%Y")  
        except IndexError:
            print "no records found in database in multiple, starting from scratch"
            pass
        print "fr_conditions, {0}\n\n\n".format(fr_conditions)
        request_return = update_database_from_fedreg(fr_base_url, fr_conditions)
        print request_return

    # generates chart from local database
    qset = FedRegDoc.objects.all()
    chart_url = generate_freq_chart_url_from_qset(qset, 600, 150) # last two parameters give size of chart graphic  
     
    return render_to_response('home.html', {"chart_url": chart_url, "search_term":search_term}, context_instance=RequestContext(request))



# --------------------------------------------------------------------------------------------------------------
#     list
#
#  shows a list of records in the local database
#
# --------------------------------------------------------------------------------------------------------------
def list_view(request, **kwargs):
    # search functionality is not implemented
    search_term = None

    # there should always be a display_num argument (i.e., number of items to display per page)    
    try:
        display_num=int(kwargs['display_num'])
        print "display_num", display_num
    except KeyError:
        print "no display number argument found"
        raise Http404

    # get list of  docs matching search term, if there is a search term; otherwise get all
    print "getting matching list of docs to search term (or all)"
    if search_term:
        doc_list = FedRegDoc.objects.filter(html_full_text__contains=search_term)
    else:
        doc_list = FedRegDoc.objects.all()

    # either get the requested doc_pk as first item to show ....  
    try:
        print "trying to get doc_pk object"
        doc_pk=int(kwargs['doc_pk'])
        # for search, need to add check here for whether doc_pk is in search result set
        doc_list = doc_list.order_by('-publication_date')
        # got to be more efficient way to do the following! (i.e., find position of doc_pk object in date-ordered list)
        for display_offset in range(doc_list.count()):
            if doc_list[display_offset].pk == doc_pk:
                break
    # ...  or if no doc_pk given, show the most recent item
    except KeyError:
        print "no doc_pk, instead retrieving most recent"
        # get the pk of the newest item by pub date
        doc_list = doc_list.order_by('-publication_date')
        doc_pk = doc_list[0].pk
        display_offset = 0
    total_doc_count = doc_list.count()        

    # set navigation parameters
    print "total_doc_count", total_doc_count
    print "setting nav parameters"
    if display_offset == 0:
        newest_pk=None
        newer_pk= None
    else:
        try:
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
    return render_to_response('list.html', {"doc_list":doc_list, 'search_term':search_term, "doc_pk":doc_pk, "display_offset": display_offset, "display_num":display_num, "newest_pk":newest_pk, "newer_pk":newer_pk, "older_pk":older_pk, "oldest_pk":oldest_pk, "total_doc_count":total_doc_count}, context_instance=RequestContext(request))


# --------------------------------------------------------------------------------------------------------------
#  detail
#
# shows details for a single fedreg document based on primary key (pk) number
# (and comments if enabled)
# --------------------------------------------------------------------------------------------------------------
def detail_view(request, **kwargs):

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
    return render_to_response('detail.html', {"doc":doc, "comment_posted":comment_posted, "newer_pk":newer_pk, "older_pk":older_pk, "newest_pk":newest_pk, "oldest_pk":oldest_pk}, context_instance=RequestContext(request))

        
# --------------------------------------------
#    visualizations
#---------------------------------------------
def vis_view(request, **kwargs):         
    trophies = []
    trophies_sorted=[]
    state_counts = {}
    state_counts_sorted = []
    state_counts_total = 0

    google_geocode_flag = False # NEED TO SET TO True TO ALLOW GEOCODING    
    trophies = extract_trophy_records_from_local(google_geocode_flag)
    
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
        state_counts_sorted.append([full_state_name_from_abbrev(k), v])
        state_counts_total += int(v)
    state_counts_sorted.sort(key=itemgetter(0))    

    # sort trophy details by date for display and place in list of lists and regularize source population names
    for t in trophies:    
        t['app_popn'] = regularize_population_name(t['app_popn'])                               
        trophies_sorted.append([t['app_date'], t['app_name_prefix'], t['app_name'], t['app_name_suffix'], t['app_city'], t['app_state'], t['app_num'], t['app_popn']]) # if using lat/lng would need to add in here for display
    trophies_sorted.sort(key=itemgetter(0))         
    
    # generate URL to map state counts using Google Map Chart 
    map_url = generate_trophy_map_chart_url(state_counts, 600, 350)
    popn_pie_chart_url = generate_pie_chart_source_popn(trophies, 600, 200)
    freq_chart_url=generate_trophy_freq_chart_url(trophies, 600, 200)
            
    return render_to_response('visualizations.html', {"trophies_sorted":trophies_sorted, "state_counts_sorted":state_counts_sorted, "state_counts_total":state_counts_total, 'map_url':map_url, 'popn_pie_chart_url':popn_pie_chart_url, "freq_chart_url": freq_chart_url}, context_instance=RequestContext(request))



# ------------------------------------------------0
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

