from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core import serializers
from django.http import Http404
from django.template import RequestContext

from fedregfeed.models import FedRegDoc, Agency
from utils import update_database_from_fedreg, generate_chart_url_from_fedreg, generate_chart_url_from_local


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
# the single view shows details for a single fedreg document based on pk number (which is already in the database)
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
     
    return render_to_response('chart.html', {"chart_url": chart_url, "search_term":search_term, "end_year":end_year, "start_year":start_year}, context_instance=RequestContext(request))
    
