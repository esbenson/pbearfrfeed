from django.conf.urls.defaults import patterns, include, url
from utils import LatestPolarBearUpdate

#------------------- number to display on list page 
display_num=10

#------------------------------------------
#---------------------------- basic views
#------------------------------------------
urlpatterns = patterns('fedregfeed.views',
    url(r'^list/(?P<doc_pk>\d+)/$', 'list_view', {'display_num':display_num}, name='pbear_list'), # calls the update/display view with custom arguments - initial record and num to display
    url(r'^list/$', 'list_view', {'display_num':display_num, 'update_database_flag':True}, name='pbear_list_default'), # calls the update/display view with default args
    url(r'^detail/(?P<doc_pk>\d+)/$', 'detail_view', name='pbear_detail_pk'), # calls the detail view for single record identified by primary key
    url(r'^visualizations/$', 'vis_view', name='pbear_vis'), # calls the visualizations view
    url(r'^$', 'home_view', {'update_database_flag':True, 'search_term':r'"polar bear"|"polar bears"'}, name='pbear_home'), # calls the home view and updates the database
)

#------------------------------------------
#------------------------------ feed and comments
#------------------------------------------
urlpatterns += patterns('fedregfeed',
    (r'^feed/$', LatestPolarBearUpdate()), # syndication    
    (r'^comments/', include('django.contrib.comments.urls')), # comments
)


#------------------------------------------
# ----------------------------- old/unused url patterns
#------------------------------------------
urlpatterns += patterns('fedregfeed',
    #    url(r'^detail/(?P<doc_pk>\d+)/comment_posted/$', 'detail_view', {'comment':True}, name='pbear_single_comment_posted'), # calls view for single record  after comment posted

#    url(r'^chart/(?P<search_term>\w+)/$', 'chart_view', {'end_year':2011, 'start_year':1994}, name='pbear_chart'),
#    url(r'^chart/$', 'chart_view', {'search_term':None, 'end_year':2011, 'start_year':1994}, name='pbear_chart'),
    
    #url(r'^add_html_full_text/$', 'add_html_full_text_to_all'), # for one-time run
)

