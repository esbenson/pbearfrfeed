from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.core import serializers
from django.http import Http404
from django.template import RequestContext
from fedregfeed.models import FedRegDoc, Agency, SearchResult
from utils import update_database_from_fedreg
    

# --------------------------------------------------------------------------------------------------------------
# the index view shows a list of records in the database (and updates the database)
# --------------------------------------------------------------------------------------------------------------
def index(request, **kwargs):
    # setup basic request (search) url
    base_url = 'http://api.federalregister.gov/v1/articles.json'
    conditions = 'conditions[term]=\"polar bear\"|\"polar bears\"'         

    # if database contains docs already, then only search for more recent items than contained in database (ie., add a "gte" condition)
    try:
        most_recent_doc_pub_date = FedRegDoc.objects.all().order_by('-publication_date')[0].publication_date
        conditions = conditions + '&' + 'conditions[publication_date][gte]=' + most_recent_doc_pub_date.strftime("%m/%d/%Y")  
    except IndexError:
        most_recent_doc_pub_date=None

    # update the database 
    request_return = update_database_from_fedreg(base_url, conditions)
    
    # select items to be displayed from database, including logic to avoid exceeding range and to allow navigation in template
    display_offset=max(0, int(kwargs['display_offset']))
    display_num=int(kwargs['display_num'])
    total_doc_count=FedRegDoc.objects.count()
    if display_offset > total_doc_count:
        raise Http404
    if (display_offset + display_num) > total_doc_count:
        display_num = total_doc_count - display_offset
    newer_offset=max(0, display_offset - display_num)
    older_offset=display_offset + display_num
    oldest_offset = max(0, total_doc_count - display_num)
    doc_list=FedRegDoc.objects.all().order_by('-publication_date')[display_offset:(display_offset + display_num)]

    # render html via template
    return render_to_response('index.html', {"doc_list":doc_list, "display_offset":display_offset, "display_num":display_num, "newer_offset":newer_offset, "older_offset":older_offset, "oldest_offset":oldest_offset, "total_doc_count":total_doc_count}, context_instance=RequestContext(request))


# --------------------------------------------------------------------------------------------------------------
# the single view shows details for a single fedreg document (which is already in the database)
# --------------------------------------------------------------------------------------------------------------
def single(request, **kwargs):

    try:
        doc_pk=int(kwargs['doc_pk'])
        doc = FedRegDoc.objects.get(pk=doc_pk)
    except KeyError:
        print "no doc_pk key passed to single view"
        raise Http404
    except FedRegDoc.DoesNotExist:    
        print "no record exists for given pk in single view", doc_pk
        raise Http404
        
    try:
        comment_posted=kwargs['comment']
    except KeyError:
        comment_posted=False
        
    return render_to_response('single.html', {"doc":doc, "comment_posted":comment_posted}, context_instance=RequestContext(request))



