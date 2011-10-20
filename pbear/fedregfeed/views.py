from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core import serializers
from django.http import Http404
from django.template import RequestContext
from fedregfeed.models import FedRegDoc, Agency, SearchResult
from utils import update_database_from_fedreg
    

# --------------------------------------------------------------------------------------------------------------
# the list view shows a list of records in the database
# --------------------------------------------------------------------------------------------------------------
def multiple(request, **kwargs):
    
    # select items to be displayed from database, including logic to avoid exceeding range and to allow navigation in template
    try:
        display_num=int(kwargs['display_num'])
    except KeyError:
        raise Http404

    try:
       doc_pk=max(0, int(kwargs['doc_pk']))
    except KeyError:
       doc_pk=None
        
    total_doc_count = FedRegDoc.objects.count()
    doc_list=list(FedRegDoc.objects.all().order_by('-publication_date'))
    if doc_pk == None:
        doc_pk = doc_list[0].pk
        
    # find offset for given doc_pk
    i = 0
    for i in range(total_doc_count):
        if doc_list[i].pk == doc_pk:
            break     
    display_offset = i
    
    newer_pk = doc_list[max(0, display_offset - display_num)].pk
    newest_pk = doc_list[0].pk
    if (display_offset + display_num) > total_doc_count:
        display_num = total_doc_count - display_offset
    older_pk = doc_list[display_offset + display_num - 1].pk
    oldest_pk = doc_list[max(0, total_doc_count - display_num)].pk
    
    doc_list=doc_list[display_offset:(display_offset + display_num)]

    # render html via template
    return render_to_response('multiple.html', {"doc_list":doc_list, "doc_pk":doc_pk, "display_offset": display_offset, "display_num":display_num, "newest_pk":newest_pk, "newer_pk":newer_pk, "older_pk":older_pk, "oldest_pk":oldest_pk, "total_doc_count":total_doc_count}, context_instance=RequestContext(request))



# --------------------------------------------------------------------------------------------------------------
# the single view shows details for a single fedreg document based on pk number (which is already in the database)
#
# --------------------------------------------------------------------------------------------------------------
def single(request, **kwargs):

    # set comment flag if this page being called after comment posted, so that "thanks" is displayed
    try:
        comment_posted=kwargs['comment']
    except KeyError:
        comment_posted=False

    # try to get the document obj to be displayed based on primary key passed in as arg
    try:
        doc_pk=int(kwargs['doc_pk'])
        doc = FedRegDoc.objects.get(pk=doc_pk)
    except KeyError:
        print "no doc_pk given to single view"
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
        # get the most recent item
        doc = FedRegDoc.objects.order_by('-publication_date')[0]
    except FedRegDoc.DoesNotExist:
        raise Http404

    # find primary key for nav to newer record
    q = list(FedRegDoc.objects.order_by('publication_date').filter(publication_date__gte = doc.publication_date).distinct())
    i = 0
    for i in range(len(q)):
        if q[i].pk == doc.pk:
            break
    try:
        newer_pk = q[i+1].pk
    except IndexError:
        newer_pk = None
        
    # find primary key for nav to older record
    q = list(FedRegDoc.objects.order_by('-publication_date').filter(publication_date__lte=doc.publication_date).distinct())
    i = 0
    for i in range(len(q)):
        if q[i].pk == doc.pk:
            break
    try:
        older_pk = q[i+1].pk
    except IndexError:
        older_pk = None    

    # find primary key for nav to oldest record
    oldest_pk = FedRegDoc.objects.order_by('publication_date')[0].pk
    # find primary key for nav to newest record
    newest_pk = FedRegDoc.objects.order_by('-publication_date')[0].pk
    if newest_pk == doc.pk:
        newest_pk = None

    # render page
    return render_to_response('single.html', {"doc":doc, "comment_posted":comment_posted, "newer_pk":newer_pk, "older_pk":older_pk, "newest_pk":newest_pk, "oldest_pk":oldest_pk}, context_instance=RequestContext(request))



