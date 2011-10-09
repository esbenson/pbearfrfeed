# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Agency'
        db.create_table('fedregfeed_agency', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('json_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('agency_original_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('raw_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('fedregfeed', ['Agency'])

        # Adding model 'FedRegDoc'
        db.create_table('fedregfeed_fedregdoc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document_type', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('document_number', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('publication_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('abstract', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('excerpts', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('json_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('html_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('pdf_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('fedregfeed', ['FedRegDoc'])

        # Adding M2M table for field agencies on 'FedRegDoc'
        db.create_table('fedregfeed_fedregdoc_agencies', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('fedregdoc', models.ForeignKey(orm['fedregfeed.fedregdoc'], null=False)),
            ('agency', models.ForeignKey(orm['fedregfeed.agency'], null=False))
        ))
        db.create_unique('fedregfeed_fedregdoc_agencies', ['fedregdoc_id', 'agency_id'])

        # Adding model 'SearchResult'
        db.create_table('fedregfeed_searchresult', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('results', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('total_pages', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('next_page_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('fedregfeed', ['SearchResult'])


    def backwards(self, orm):
        
        # Deleting model 'Agency'
        db.delete_table('fedregfeed_agency')

        # Deleting model 'FedRegDoc'
        db.delete_table('fedregfeed_fedregdoc')

        # Removing M2M table for field agencies on 'FedRegDoc'
        db.delete_table('fedregfeed_fedregdoc_agencies')

        # Deleting model 'SearchResult'
        db.delete_table('fedregfeed_searchresult')


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
            'html_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'pdf_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'publication_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        'fedregfeed.searchresult': {
            'Meta': {'object_name': 'SearchResult'},
            'count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'next_page_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'results': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'total_pages': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fedregfeed']
