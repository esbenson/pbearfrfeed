from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from fedregfeed.models import FedRegDoc, Agency, SearchResult
from django.core import serializers
from urllib2 import urlopen, quote
import json
from django.http import Http404
from django.template import RequestContext

def index(request, **kwargs):
    # define base url and search conditions and combine into request_url
    base_request_url = 'http://api.federalregister.gov/v1/articles.json'
    # check to see if there are existing records, and if so, grab the most recent pub date  
    try:
        most_recent_doc_pub_date = FedRegDoc.objects.all().order_by('-publication_date')[0].publication_date
    except IndexError:
        most_recent_doc_pub_date=None
    
    # setup basic request (search) url
    request_conditions = 'conditions[term]=\"polar bear\"|\"polar bears\"'         
    # if database contains docs already, then only search for more recent items than contained in database
    if most_recent_doc_pub_date is not None:
        request_conditions = request_conditions + '&' + 'conditions[publication_date][gte]=' + most_recent_doc_pub_date.strftime("%m/%d/%Y")  
    request_url = base_request_url + '?' + quote(request_conditions, safe='/:+=?&"|')
  
    #save the original request to pass to the template later
    original_request_url=request_url
    
    # open the URL, grab first (or next) page of JSON response, deserialize JSON into dictionary, extract 'results' field (doc data)
    # loop as long as there are additional pages to grab 
    while request_url is not None:
        # open url, read, and deserialize JSON source
        fedregsource = urlopen(request_url)
        jsondata = fedregsource.read()
        fedregsource.close()
        deserialized_return=json.loads(jsondata)
        
        # following lines print to console for debugging
        print ("request_url: ", request_url)
        print ("count: ", deserialized_return['count'])

        # check to make sure that the search returned some results
        if deserialized_return['count'] is not 0:
            
            results=deserialized_return['results']

            # iterate through results, create new objects, and save to database
            for d in results:
                # load next document from results and, if new, save to database
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
         
            # extract information about the number of pages/items/next_page_url
            # if next page urls exists -- then set request_url to next_page_url and loop back to beginning of 'while' statement 
            request_return = SearchResult(results=deserialized_return['results'], count=deserialized_return['count'], total_pages=deserialized_return['total_pages'])
            try:
                request_return.next_page_url=deserialized_return['next_page_url']
            except KeyError:
                request_return.next_page_url=None
            request_url = request_return.next_page_url
        else:
            print("count was 0, no results of search using ", original_request_url)
       
    
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

    # render
    return render_to_response('index.html', {"request_url":original_request_url, "request_return":request_return, "doc_list":doc_list, "display_offset":display_offset, "display_num":display_num, "newer_offset":newer_offset, "older_offset":older_offset, "oldest_offset":oldest_offset, "total_doc_count":total_doc_count}, context_instance=RequestContext(request))

