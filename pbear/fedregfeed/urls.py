from django.conf.urls.defaults import patterns, include, url
from utils import LatestPolarBearUpdate

urlpatterns = patterns('fedregfeed.views',
    url(r'^(?P<display_offset>\d+)/(?P<display_num>\d+)/$', 'index'), # calls the update/display view with custom arguments - initial record and num to display
    url(r'^(?P<doc_pk>\d+)/comment_posted/$', 'single', {'comment':True}, name='pbear_comment_posted'), # calls the detail view for single record  after comment posted
    url(r'^(?P<doc_pk>\d+)/$', 'single'), # calls the detail view for single record 
    url(r'^$', 'index', {'display_offset':0, 'display_num':20}, name='pbear_index'), # calls the update/display view with default arguments (i.e., show the beginning of the list)
)

urlpatterns += patterns('fedregfeed',
    (r'^feed/$', LatestPolarBearUpdate()), # syndication    
    (r'^comments/', include('django.contrib.comments.urls')), # comments
)

#following are legacy, to maintain access to urls as initially posted
urlpatterns += patterns('fedregfeed',
    (r'^fedregfeed/feed/$', LatestPolarBearUpdate()), # syndication
    url(r'^fedregfeed/$', 'views.index', {'display_offset':0, 'display_num':20}) # calls the update/display view with default arguments (i.e., show the beginning of the list)
)
 
  
