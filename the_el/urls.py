from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns(
    '',
    url(r'^$', 'the_el.views.index', name='index'),
    url(r'routes/(?P<pkey>\d+)$', 'the_el.views.route', name='route'),
    url(r'routes_json/(?P<pkey>\d+)$', 'the_el.views.route_json', name='route_json'),
    url(r'^admin/', include(admin.site.urls)),
)
