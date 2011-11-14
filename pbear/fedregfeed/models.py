from django.db import models
from django.contrib.comments.moderation import CommentModerator, moderator
    
class Agency(models.Model):
    url=models.CharField(max_length=200, null=True, blank=True)
    json_url=models.CharField(max_length=200, null=True, blank=True)
    name=models.CharField(max_length=200, null=True, blank=True)
    agency_original_id=models.IntegerField(null=True, blank=True)
    raw_name=models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
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
    html_full_text = models.TextField(null=True, blank=True)
    # add field for pdf binary?
    # add field for json?

    def __unicode__(self):
        return self.title

class FedRegDocGloss(models.Model):
    doc=models.ForeignKey(FedRegDoc)
    title=models.CharField(max_length=500)
    datetime=models.DateTimeField()
    content=models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.title

class FedRegDocModerator(CommentModerator):
    email_notification = False
 #   auto_close_field   = 'posted_date'
    # Close the comments after 7 days.
  #  close_after        = 7

moderator.register(FedRegDoc, FedRegDocModerator)
