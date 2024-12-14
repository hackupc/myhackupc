from django.conf.urls import url

from whoareu import views

urlpatterns = [
    url(r'^$', views.WhoAreU.as_view(), name='whoareu'),
    url(r'api/$', views.WhoAreUAPI.as_view(), name='whoareu-api')
]
