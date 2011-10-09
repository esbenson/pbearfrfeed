from django.contrib.syndication.views import Feed
from fedregfeed.models import FedRegDoc, Agency
from datetime import datetime, time

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
