from django.urls import reverse
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from user.mixins import IsVolunteerMixin
from app.mixins import TabsViewMixin
from user.models import User
from hardware.models import Item, ItemType, Lending

def hardware_tabs(user):
    first_tab = ('Hardware List', reverse('hw_list'), False)
    if user.is_volunteer:
        first_tab = ('Hardware Admin', reverse('hw_admin'), False)
    return [
        first_tab,
        ('Log', reverse('hw_log'), False)
    ]

class HardwareListView(LoginRequiredMixin, TabsViewMixin, TemplateView):
    template_name = 'hardware_list.html'

    def get_current_tabs(self):
        return hardware_tabs(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(HardwareListView, self).get_context_data(**kwargs)
        context['hw_list'] = ItemType.objects.all()
        return context

    def post(self, request):
        if request.is_ajax:
            if 'req_item' in request.POST:
                item = ItemType.objects.get(id=request.POST['item_id'])
                if item.get_available_count() > 0:
                    item.make_request(request.user)
                    return JsonResponse({'ok':True})

                return JsonResponse({'error': 'Item unavailable'})

class HardwareAdminView(IsVolunteerMixin, TabsViewMixin, TemplateView):
    template_name = 'hardware_admin.html'

    def post(self, request):
        if request.is_ajax:
            if 'getlist' in request.POST:
                target_user = User.objects.get(email=request.POST['email'])
                requests = Request.objects.get_active_by_user(target_user)
                request_dicts = [l.to_list_item() for l in requests]
                lendings = Lending.objects.get_active_by_user(target_user)
                lending_dicts = [l.to_list_item() for l in lendings]
                data = {
                    'requests': request_dicts,
                    'lendings': lending_dicts
                }
                return JsonResponse(data)


    def get_current_tabs(self):
        return hardware_tabs(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(HardwareAdminView, self).get_context_data(**kwargs)
        context['hw_list'] = ItemType.objects.all()
        return context