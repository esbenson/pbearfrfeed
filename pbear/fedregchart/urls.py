from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('fedregchart.views',
    url(r'^$', 'show_chart', name='chart_default'), 
)

