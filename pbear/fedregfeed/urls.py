from django.conf.urls.defaults import patterns, include, url
from utils import LatestPolarBearUpdate

urlpatterns = patterns('fedregfeed.views',
    url(r'^list/(?P<doc_pk>\d+)/$', 'multiple', {'display_num':20}, name='pbear_list'), # calls the update/display view with custom arguments - initial record and num to display
    url(r'^single/(?P<doc_pk>\d+)/comment_posted/$', 'single', {'comment':True}, name='pbear_single_comment_posted'), # calls view for single record  after comment posted
    url(r'^single/(?P<doc_pk>\d+)/$', 'single', name='pbear_single_pk'), # calls the detail view for single record 
    url(r'^list/$', 'multiple', {'display_num':20}, name='pbear_list_default'), # calls the update/display view with custom arguments - initial record and num to display
    url(r'^$', 'multiple', {'display_num':20}, name='pbear_list_default'), # calls the update/display view with default arguments - (no pk) and num to display
    #url(r'^$', 'single', name='pbear_single_default'), 
)

urlpatterns += patterns('fedregfeed',
    (r'^feed/$', LatestPolarBearUpdate()), # syndication    
    (r'^comments/', include('django.contrib.comments.urls')), # comments
)

