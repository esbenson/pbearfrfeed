from django.conf.urls.defaults import patterns, include, url
from utils import FRFeed, BlogFeed

#------------------- number to display on list page 
display_num=20

#------------------------------------------
#      basic views
#------------------------------------------
urlpatterns = patterns('fedregfeed.views',
    url(r'^list/(?P<doc_pk>\d+)/$', 'list_view', {'display_num':display_num}, name='pbear_list'), # calls the update/display view with custom arguments - initial record and num to display
    url(r'^list/$', 'list_view', {'display_num':display_num, 'update_database_flag':True}, name='pbear_list_default'), # calls the update/display view with default args
    url(r'^detail/(?P<doc_pk>\d+)/$', 'detail_view', name='pbear_detail_pk'),  #detail
    url(r'^detail/(?P<doc_pk>\d+)/(?P<search_term>.+)/(?P<display_page>\d+)/$', 'detail_view', name='pbear_detail_pk_search'), #detail
    url(r'^visualizations/$', 'vis_view', name='pbear_vis'), # visualizations
    url(r'^$', 'home_view', {'update_database_flag':True, 'search_term':r'"polar bear"|"polar bears"'}, name='pbear_home'), # home
    url(r'^search/(?P<search_term>.+)/(?P<display_page>\d+)/$', 'search_view', {'num_per_page':display_num}, name='pbear_search_term_page'), 
    url(r'^search/(?P<search_term>.+)/$', 'search_view', {'num_per_page':display_num}, name='pbear_search_term'), 
    url(r'^search/$', 'search_view', {'num_per_page':display_num, 'display_page': 1}, name='pbear_search_default'),
    url(r'^search/$', 'search_view', {'num_per_page':display_num}, name='pbear_search_no_args'), 
    url(r'^browse/(?P<display_page>\d+)/$', 'search_view', {'show_all':True, 'num_per_page':display_num}, name='pbear_browse_page'),
    url(r'^browse/$', 'search_view', {'show_all':True, 'num_per_page':display_num}, name='pbear_browse'),
    url(r'^blog/(?P<display_page>\d+)/$', 'blog_list_view', {}, name='blog_list_view_page'),
    url(r'^blog/$', 'blog_list_view', {}),
    url(r'^blog/detail/(?P<post_pk>\d+)/$', 'blog_single_view', {}, name='blog_single_view'),
    )

#------------------------------------------
#------------------------------ feeds and comments
#------------------------------------------
urlpatterns += patterns('fedregfeed',
    (r'^feed/$', FRFeed()), # syndication    
    (r'^blog/feed/$', BlogFeed()), # syndication    
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

