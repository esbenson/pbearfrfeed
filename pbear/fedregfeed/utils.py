from django.contrib.syndication.views import Feed
from urllib2 import urlopen, quote
import json
from fedregfeed.models import FedRegDoc, Agency, SearchResult

class LatestPolarBearUpdate(Feed):
    title="Polar Bear FedReg Feed"
    link="/feed/"
    description="Latest notices, rules, and proposed rules from the Federal Register featuring polar bears." 
    
    def items(self):
        return FedRegDoc.objects.order_by('-publication_date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.abstract
        
    def item_link(self, item):
        return item.html_url
        
    def item_pubdate(self, item):
        return datetime.combine(item.publication_date, time())
        
    def item_categories(self, item):
        return item.document_type
        
def update_database_from_fedreg(base_url, conditions):
    request_url = base_url + '?' + quote(conditions, safe='/:+=?&"|')

    while request_url is not None:
        # open url, read, and deserialize JSON source
        fedregsource = urlopen(request_url)
        jsondata = fedregsource.read()
        fedregsource.close()
        deserialized_return=json.loads(jsondata)
        
        # following lines print to console for debugging
        print "request_url: ", request_url
        print "count: ", deserialized_return['count']

        # check to make sure that the search returned some results
        if deserialized_return['count'] is not 0:
        
            # iterate through results, create new objects, and save to database
            for d in deserialized_return['results']:
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
            request_return = SearchResult(results=deserialized_return['results'], count=deserialized_return['count'], total_pages=deserialized_return['total_pages'])
            try:
                request_url=deserialized_return['next_page_url']
            except KeyError:
                request_url=None
                
            # return to beginning of while loop (will break if request_url=None)
                
    return request_return
