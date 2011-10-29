# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'SearchResult'
        db.delete_table('fedregfeed_searchresult')

        # Adding field 'FedRegDoc.html_full_text'
        db.add_column('fedregfeed_fedregdoc', 'html_full_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'SearchResult'
        db.create_table('fedregfeed_searchresult', (
            ('count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('total_pages', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('results', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('next_page_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('fedregfeed', ['SearchResult'])

        # Deleting field 'FedRegDoc.html_full_text'
        db.delete_column('fedregfeed_fedregdoc', 'html_full_text')


    models = {
        'fedregfeed.agency': {
            'Meta': {'object_name': 'Agency'},
            'agency_original_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'raw_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'fedregfeed.fedregdoc': {
            'Meta': {'object_name': 'FedRegDoc'},
            'abstract': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'agencies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['fedregfeed.Agency']", 'null': 'True', 'blank': 'True'}),
            'document_number': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'document_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'excerpts': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'html_full_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'html_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'pdf_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'publication_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fedregfeed']
