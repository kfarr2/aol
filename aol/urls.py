from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings as SETTINGS
from aol.lakes import views as lakes
from aol.home import views as home
from aol.maps import views as maps
from aol.users import views as customadmin
from aol.documents import views as documents
from aol.photos import views as photos

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', home.home, name='home'),
	url(r'^search/?$', lakes.search, name='lakes-search'),

    url(r'^lakes/?$', lakes.listing, name='lakes-listing'),
    url(r'^lakes/(?P<letter>[a-z])/?$', lakes.listing, name='lakes-listing'),
    url(r'^lakes/(?P<reachcode>.+)?$', lakes.detail, name='lakes-detail'),
    url(r'^plants/csv/(?P<reachcode>.+)?$', lakes.plants_csv, name='plants-csv'),

    url(r'^map/?$', maps.home, name='map'),
    url(r'^map/search/?$', maps.search, name='map-search'),
    url(r'^map/lakes\.kml$', maps.lakes, name='lakes-kml'),
    url(r'^map/facilities\.kml$', maps.facilities, name='facilities-kml'),
    url(r'^maps/panel/(?P<reachcode>.+)?$', maps.panel, name='lakes-panel'),

    # admin area
    url(r'^admin/?$', customadmin.listing, name='admin-listing'),
    url(r'^admin/edit/lake/(?P<reachcode>.+)?$', customadmin.edit_lake, name='admin-edit-lake'),
    url(r'^admin/edit/photo/(?P<photo_id>\d+)?$', photos.edit, name='admin-edit-photo'),
    url(r'^admin/edit/flatpage/(?P<pk>\d+)?$', customadmin.edit_flatpage, name='admin-edit-flatpage'),
    url(r'^admin/add/photo/(?P<reachcode>.+)?$', photos.edit, name='admin-add-photo'),
    url(r'^admin/edit/document/(?P<document_id>\d+)?$', documents.edit, name='admin-edit-document'),
    url(r'^admin/add/document/(?P<reachcode>.+)?$', documents.edit, name='admin-add-document'),
    url(r'^admin/add/flatpage/?$', customadmin.edit_flatpage, name='admin-add-flatpage'),
    
    # login logout
    url(r'^admin/login/$', 'djangocas.views.login', name='admin-login'),
    url(r'^admin/logout/$', 'djangocas.views.logout', name='admin-logout', kwargs={"next_page": "/"}),

    # documents
    url(r'^documents/download/(?P<document_id>.+)?$', documents.download, name='documents-download'),


    # Examples:
    # url(r'^$', 'aol.views.home', name='home'),
    # url(r'^aol/', include('aol.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
) + static(SETTINGS.MEDIA_URL, document_root=SETTINGS.MEDIA_ROOT)
