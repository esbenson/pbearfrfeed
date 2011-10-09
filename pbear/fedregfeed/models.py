from django.contrib.gis.db import models

    
class Agency(models.Model):
    url=models.CharField(max_length=200, null=True, blank=True)
    json_url=models.CharField(max_length=200, null=True, blank=True)
    name=models.CharField(max_length=200, null=True, blank=True)
    agency_original_id=models.IntegerField(null=True, blank=True)
    raw_name=models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.raw_name

class FedRegDoc(models.Model):
    document_type=models.CharField(max_length=50, null=True, blank=True)
    document_number=models.CharField(max_length=50, null=True, blank=True)
    title=models.CharField(max_length=500, null=True, blank=True)
    publication_date=models.DateField(null=True, blank=True)
    agencies=models.ManyToManyField(Agency, null=True, blank=True)
    abstract=models.TextField(null=True, blank=True)
    excerpts=models.TextField(null=True, blank=True)
    json_url=models.CharField(max_length=200, null=True, blank=True)
    html_url=models.CharField(max_length=200, null=True, blank=True)
    pdf_url=models.CharField(max_length=200, null=True, blank=True)
        
    def __unicode__(self):
        return self.title
    
class SearchResult(models.Model):
    results=models.TextField(null=True, blank=True)
    count=models.IntegerField(null=True, blank=True)
    total_pages=models.IntegerField(null=True, blank=True)
    next_page_url=models.CharField(max_length=200, null=True, blank=True)
       

