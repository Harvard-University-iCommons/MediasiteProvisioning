from django.conf.urls import url

from . import views

app_name = 'web'

urlpatterns = [
    url(r'^$', views.search, name='index'),
    url(r'provision', views.provision, name='provision'),
    url(r'oauth', views.oauth, name='oauth'),
]
