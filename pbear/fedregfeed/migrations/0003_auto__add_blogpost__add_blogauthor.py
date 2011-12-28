# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BlogPost'
        db.create_table('fedregfeed_blogpost', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime', self.gf('django.db.models.fields.DateTimeField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fedregfeed.BlogAuthor'])),
        ))
        db.send_create_signal('fedregfeed', ['BlogPost'])

        # Adding model 'BlogAuthor'
        db.create_table('fedregfeed_blogauthor', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('fedregfeed', ['BlogAuthor'])


    def backwards(self, orm):
        
        # Deleting model 'BlogPost'
        db.delete_table('fedregfeed_blogpost')

        # Deleting model 'BlogAuthor'
        db.delete_table('fedregfeed_blogauthor')


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
        'fedregfeed.blogauthor': {
            'Meta': {'object_name': 'BlogAuthor'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'fedregfeed.blogpost': {
            'Meta': {'object_name': 'BlogPost'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fedregfeed.BlogAuthor']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'})
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
