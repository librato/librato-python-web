from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'notfound/$', views.error_notfound, name='error_notfound'),
    url(r'error/$', views.error_5xx, name='error_5xx'),
    url(r'exception/$', views.error_exception, name='error_exception'),
]
