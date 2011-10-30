from django.conf.urls.defaults import patterns, include, url
from utils import LatestPolarBearUpdate

display_num=10

urlpatterns = patterns('fedregfeed.views',
    url(r'^list/(?P<doc_pk>\d+)/$', 'multiple', {'display_num':display_num}, name='pbear_list'), # calls the update/display view with custom arguments - initial record and num to display
    url(r'^list/$', 'multiple', {'display_num':display_num}, name='pbear_list_default'), # calls the update/display view with custom arguments - initial record and num to display
    url(r'^single/(?P<doc_pk>\d+)/comment_posted/$', 'single', {'comment':True}, name='pbear_single_comment_posted'), # calls view for single record  after comment posted
    url(r'^single/(?P<doc_pk>\d+)/$', 'single', name='pbear_single_pk'), # calls the detail view for single record 
    url(r'^chart/$', 'pbear_chart', {'search_term':'\"polar bear\"|\"polar bears\"', 'end_year':2011, 'start_year':1994}, name='pbear_chart'),
    url(r'^$', 'multiple', {'display_num':display_num}, name='pbear_list_default'), # calls the update/display view with default arguments - (no pk) and num to display
    url(r'^add_html_full_text/$', 'add_html_full_text_to_all'),
    url(r'^trophy/$', 'show_trophy', name='pbear_trophy_map'),
)

urlpatterns += patterns('fedregfeed',
    (r'^feed/$', LatestPolarBearUpdate()), # syndication    
    (r'^comments/', include('django.contrib.comments.urls')), # comments
)

