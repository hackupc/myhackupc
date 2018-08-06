from django.urls import reverse
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from user.mixins import IsVolunteerMixin
from app.mixins import TabsViewMixin
from user.models import User
from hardware.models import Item, ItemType, Lending, Request

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
        requests = Request.objects.get_active_by_user(self.request.user)
        context['requests'] = {x.item_type.id:x.get_remaining_time() for x in requests}
        return context

    def req_item(self, request):
        item = ItemType.objects.get(id=request.POST['item_id'])
        if item.get_available_count() > 0:
            item.make_request(request.user)
            return JsonResponse({'ok':True})

        return JsonResponse({'msg': "ERROR: There are no items available"})

    def post(self, request):
        if request.is_ajax:
            if 'req_item' in request.POST:
                return self.req_item(request)

class HardwareAdminView(IsVolunteerMixin, TabsViewMixin, TemplateView):
    template_name = 'hardware_admin.html'

    def get_lists(self, request):
        target_user = User.objects.get(email=request.POST['email'])
        if target_user:
            requests = Request.objects.get_active_by_user(target_user)
            lendings = Lending.objects.get_active_by_user(target_user)
            html = render_to_string("include/hardware_admin_user.html",{
                'requests':requests,
                'lendings':lendings
            })
            return JsonResponse({
                'content':html
            })
        else:
            html = render_to_string("include/hardware_admin_init.html", {
                    'hw_list':ItemType.objects.all(),
            })
            return JsonResponse({
                'content':html,
                'msg': "The user doesn't exist"
            })
        
    def select_request(self, request):
        request_obj = Request.objects.get(id=request.POST['request_id'])
        if request_obj.is_active():
            available_items = request_obj.item_type.get_lendable_items()
            html = render_to_string("include/hardware_admin_lending.html", {
                    'items':available_items,
                    'request_id':request.POST['request_id']
            })
            return JsonResponse({'content':html})
        else:
            html = render_to_string("include/hardware_admin_init.html", {
                    'hw_list':ItemType.objects.all(),
            })
            return JsonResponse({
                'content':html,
                'msg': "ERROR: The request has expired"
            })
        
    def return_item(self, request):
        lending = Lending.objects.get(id=request.POST['lending_id'])
        if lending.is_active():
            lending.return_time = timezone.now()
            lending.save()
            html = render_to_string("include/hardware_admin_init.html", {
                    'hw_list':ItemType.objects.all(),
                })
            return JsonResponse({
                'content':html,
                'msg': "The item has been returned succesfully"
            })
        else:
            html = render_to_string("include/hardware_admin_init.html", {
                    'hw_list':ItemType.objects.all(),
                })
            return JsonResponse({
                'content':html,
                'msg': "ERROR: The item was not lent"
            })

    def make_lending(self, request):
        item = Item.objects.get(id=request.POST['item_id'])
        request_obj = Request.objects.get(id=request.POST['request_id'])
        lending = Lending(user=request_obj.user, item=item)
        lending.save()
        request_obj.lending = lending
        request_obj.save()
        html = render_to_string("include/hardware_admin_init.html", {
                    'hw_list':ItemType.objects.all(),
                })
        return JsonResponse({
            'content':html,
            'msg': "The item has been lent succesfully"
        })

    def post(self, request):
        if request.is_ajax:
            if 'get_lists' in request.POST:
                return self.get_lists(request)
            if 'select_request' in request.POST:
                return self.select_request(request)
            if 'return_item' in request.POST:
                return self.return_item(request)
            if 'make_lending' in request.POST:
                return self.make_lending(request)

    def get_current_tabs(self):
        return hardware_tabs(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(HardwareAdminView, self).get_context_data(**kwargs)
        context['hw_list'] = ItemType.objects.all()
        return context