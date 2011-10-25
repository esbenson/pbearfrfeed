from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('fedregchart.views',
    url(r'^$', 'chart', name='pbear_chart_default'), 
)

