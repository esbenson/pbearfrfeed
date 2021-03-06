from django import forms
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.http import Http404
from django.template import RequestContext

from urllib2 import urlopen, quote, unquote
from operator import itemgetter
import re, json, datetime
#import pylibmc, os

from fedregfeed.models import FedRegDoc, BlogPost
from utils import update_database_from_fedreg, full_state_name_from_abbrev, abbrev_state_name_from_full, regularize_population_name, extract_trophy_records_from_local, google_geocode, fr_xml_to_html, correct_errors_in_trophy_source
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
    #print "in home"

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
        #print "updating database"
        fr_base_url = 'http://api.federalregister.gov/v1/articles.json'
        fr_conditions = 'conditions[term]=' + search_term         
        try:
            most_recent_doc_pub_date = FedRegDoc.objects.all().order_by('-publication_date')[0].publication_date
            fr_conditions = fr_conditions + '&' + 'conditions[publication_date][gte]=' + most_recent_doc_pub_date.strftime("%m/%d/%Y")  
        except IndexError:
            print "no records found in database in multiple, starting from scratch"
            pass
        #print "fr_conditions, {0}\n\n\n".format(fr_conditions)
        request_return = update_database_from_fedreg(fr_base_url, fr_conditions)
        #print request_return

    # most recent item    
    most_recent_doc = FedRegDoc.objects.all().order_by('-publication_date')[0]
    
    # generates chart from local database
    qset = FedRegDoc.objects.all()
    record_count = qset.count()
    chart_url = generate_freq_chart_url_from_qset(qset, 600, 150) # last two parameters give size of chart graphic  
     
    return render_to_response('home.html', {"chart_url": chart_url, "search_term":search_term, 'record_count':record_count, "most_recent_doc":most_recent_doc}, context_instance=RequestContext(request))

# --------------------------------------------------------------------------------------------------------------
#  detail
#
# shows details for a single fedreg document 
# --------------------------------------------------------------------------------------------------------------
def detail_view(request, **kwargs):

    # set defaults
    doc_pk = None
    search_term = None
    display_page = None
    show_all = True

    # get arguments from kwargs
    for k,v in kwargs.iteritems():
        if k == 'doc_pk':
            doc_pk = int(v)
        elif k == 'search_term':
            search_term = v
        elif k == 'show_all':
            show_all = v
        elif k == 'display_page':
            display_page = int(v)
        else:
            print "invalid argument - ", k, " - passed to detail view"
            raise Http404

    # get doc from database
    try:
        doc = FedRegDoc.objects.get(pk=doc_pk)
    except:
        raise Http404

    # fulltext conversion
    if doc.xml_full_text:
        fulltext = fr_xml_to_html(doc.xml_full_text)
    else:
        print "using body html text"
        fulltext = doc.body_html_full_text
        if fulltext:
            fulltext = re.sub(r'<h3>Full text</h3>', '', fulltext) 
    
    # render page
    return render_to_response('detail.html', {"doc":doc, 'show_all':show_all, 'search_term':search_term, 'display_page':display_page, 'fulltext':fulltext}, context_instance=RequestContext(request))

        
# --------------------------------------------
#    visualizations
#---------------------------------------------
def vis_view(request, **kwargs):         
    trophies = []
    trophies_sorted = []
    state_counts = {}
    state_counts_dicts = []
    state_counts_total = 0

    google_geocode_flag = False # NEED TO SET TO True TO ALLOW GEOCODING    
    trophies = extract_trophy_records_from_local(google_geocode_flag)
    minyear = trophies[0]['app_date'].year
    maxyear = minyear
    
    # sum number of permit apps per state
    for t in trophies:
        for k,v in t.iteritems():
            if k == 'app_state':
                if v != None:
                    if state_counts.get(v):
                        state_counts[v] += 1
                    else:
                        state_counts[v] = 1
    for k,v in state_counts.iteritems():
        state_counts_dicts.append({"state":full_state_name_from_abbrev(k), "count":v})
        state_counts_total += int(v)

    # sort trophy details by date for display and place in list of lists and regularize source population names
    for t in trophies:    
        t['app_popn'] = regularize_population_name(t['app_popn'])                               
        trophies_sorted.append([t['app_date'], t['app_name_prefix'], t['app_name'], t['app_name_suffix'], t['app_city'], t['app_state'], t['app_num'], t['app_popn']]) # if using lat/lng would need to add in here for display
        if t['app_date'].year < minyear:
            minyear = t['app_date'].year
        if t['app_date'].year > maxyear:
            maxyear = t['app_date'].year
    trophies_sorted.sort(key=itemgetter(0))
        
    # generate URL to map state counts using Google Map Chart 
    map_url = generate_trophy_map_chart_url(state_counts, 600, 350)
    popn_pie_chart_url = generate_pie_chart_source_popn(trophies, 600, 200)
    freq_chart_url=generate_trophy_freq_chart_url(trophies, 600, 200)
            
    return render_to_response('visualizations.html', {"trophies_sorted":trophies_sorted, "state_counts_dicts":state_counts_dicts, "state_counts_total":state_counts_total, 'map_url':map_url, 'popn_pie_chart_url':popn_pie_chart_url, "freq_chart_url": freq_chart_url, "minyear":minyear, "maxyear":maxyear}, context_instance=RequestContext(request))

# -------------------------------------------------
#     search form
# -------------------------------------------------
class SearchForm(forms.Form):
    search_term = forms.CharField(max_length=200)

# -------------------------------------------------
#    search view
#--------------------------------------------------
def search_view(request, **kwargs):
    '''search_view for polar bear feed '''

    default_num_per_page=10
    default_display_page=1
    search_term = None
    quoted_search_term=None
    display_qset = None
    display_offset = None
    pages = None
    total_pages = 0
    total_records = 0
    page_range = []
    show_all = False

    try:
        num_per_page=int(kwargs['num_per_page'])
    except:
        num_per_page=default_num_per_page
    try:
        display_page=int(kwargs['display_page'])
        if display_page < 1:
            raise Http404
    except:
        display_page=default_display_page
    try:
        show_all = kwargs['show_all']
    except:
        show_all = False
    if not search_term:
        try:
            search_term = kwargs['search_term']
        except:
            search_term = None
                
    # if result of search form submission, process form parameter
    if request.method == 'POST':
        print "in post"
        form = SearchForm(request.POST)
        if form.is_valid():
            print "form is valid"
            search_term = unquote(form.cleaned_data['search_term'])
            show_all = False
        else:
            print "form is not valid"

    # if NOT result of form submission, get args & set up form for display
    else:
        form = SearchForm()

    if search_term:
        search_term = search_term.strip()
        if search_term == 'None':
            search_term = None
            show_all = True
        else:
            quoted_search_term = quote(search_term)
            #print "search term: ", search_term
            #print "quoted search term: ", quoted_search_term
   
    # either show all or carry out search
    #print "show all = {0}".format(show_all)
    if show_all:
        form = None
        qset = FedRegDoc.objects.all().order_by('-publication_date')
        print qset.count()
    else:
        if search_term:
            # this should be replaced with an index-based search rather than searching the FedRegDoc records directly
            qset = FedRegDoc.objects.filter(html_full_text__icontains=search_term).order_by('-publication_date')
        else:
            qset=None
    if qset:
        #print "calculating pages"
        total_records = qset.count()
        if total_records != 0:
            total_pages = total_records / num_per_page
            if total_records % num_per_page > 0:
                total_pages += 1
            page_range = range(1, total_pages + 1)
            display_offset = (display_page - 1) * num_per_page 
            if display_offset < total_records:
                #print display_offset, num_per_page, total_records
                if display_offset + num_per_page >= total_records:
                    display_qset = qset[display_offset:total_records]
                    #print "a display_qset.count()={0}".format(display_qset.count())
                else:
                    display_qset = qset[display_offset:display_offset + num_per_page]
                    #print "b display_qset.count()={0}".format(display_qset.count())
            else:
                print "error: display_offset >= total_records in search"
                raise Http404
    else:
        print "qset empty in search"

    #print "display_page {0}".format(display_page)

    return render_to_response('search.html', {'display_qset':display_qset, 'display_page':display_page, 'num_per_page':num_per_page, 'search_term':search_term, 'quoted_search_term':quoted_search_term, 'total_records':total_records, 'total_pages':total_pages, 'page_range':page_range, 'form':form, 'display_offset':display_offset}, context_instance=RequestContext(request))



# ------------------------------------------------
#    blog list view
# ------------------------------------------------
def blog_list_view(request, **kwargs):
    ''' '''
    
    try:
        display_page = int(kwargs['display_page'])
    except:
        display_page = 1
    try:
        num_per_page = int(kwargs['num_per_page'])
    except:
        num_per_page = 10
    try:
        excerpt_length = int(kwargs['excerpt_length'])
    except:
        excerpt_length = 500
    excerpt_slice = "0:" + str(excerpt_length)
    
    posts = BlogPost.objects.all().order_by('-datetime')
    total_posts = posts.count()
    display_offset = (display_page - 1) * num_per_page
    if (display_offset + num_per_page) > total_posts:
        posts_to_display = posts[display_offset:total_posts] 
        more_flag = False
    else:
        posts_to_display = posts[display_offset:display_offset + num_per_page]
        if (display_offset + num_per_page) < total_posts:
            more_flag = True
        else:
            more_flag = False

    return render_to_response('blog_list.html', {'posts_to_display':posts_to_display, 'total_posts':total_posts, 'display_page':display_page, 'num_per_page':num_per_page, 'excerpt_length':excerpt_length, 'excerpt_slice':excerpt_slice, 'more_flag':more_flag}, context_instance=RequestContext(request))


# ------------------------------------------------
# blog single-post view
# ------------------------------------------------
def blog_single_view(request, **kwargs):
    try:
        post_pk = int(kwargs['post_pk'])
    except:
        print 'no post_pk given'
        raise Http404
    post = BlogPost.objects.get(pk=post_pk)

    return render_to_response('blog_single.html', {'post':post}, context_instance=RequestContext(request))


