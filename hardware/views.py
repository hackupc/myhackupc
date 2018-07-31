from django.urls import reverse
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from app.mixins import TabsViewMixin
from hardware.models import ItemType

class HardwareListView(LoginRequiredMixin, TabsViewMixin, TemplateView):
	template_name = 'hardware_list.html'
	def get_current_tabs(self):
		return [
			('Hardware List', reverse('hw_list'), False),
			('Log', reverse('hw_log'), False)
		]
	def get_context_data(self, **kwargs):
		context = super(HardwareListView, self).get_context_data(**kwargs)
		context['hw_list'] = ItemType.objects.all()
		return context
