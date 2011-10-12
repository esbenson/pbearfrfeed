from django.conf.urls.defaults import patterns, include, url
from utils import LatestPolarBearUpdate

urlpatterns = patterns('fedregfeed',
    url(r'^(?P<display_offset>\d+)/(?P<display_num>\d+)/$', 'views.index'), # calls the update/display view with custom arguments 
    url(r'^$', 'views.index', {'display_offset':0, 'display_num':20}), # calls the update/display view with default arguments (i.e., show the beginning of the list)
    url(r'^fedregfeed/$', 'views.index', {'display_offset':0, 'display_num':20}), # calls the update/display view with default arguments (i.e., show the beginning of the list)
    (r'^feed/$', LatestPolarBearUpdate()), # syndication
    (r'^fedregfeed/feed/$', LatestPolarBearUpdate()), # syndication
 )
