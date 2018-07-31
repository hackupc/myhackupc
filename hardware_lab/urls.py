from django.conf.urls import url
from hardware_lab import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^list/$', views.HardwareListView.as_view(), name='hw_lab_list'),
    url(r'^log/$', views.HardwareListView.as_view(), name='hw_lab_log')
]