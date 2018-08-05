from django.urls import reverse
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
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
            if 'get_lists' in request.POST:
                target_user = User.objects.get(email=request.POST['email'])
                requests = Request.objects.get_active_by_user(target_user)
                lendings = Lending.objects.get_active_by_user(target_user)
                
                return HttpResponse(render_to_string("include/hardware_admin_user.html",{
                    'requests':requests,
                    'lendings':lendings
                }))
            if 'select_request' in request.POST:
                request_obj = Request.objects.get(id=request.POST['request_id'])
                if request_obj.is_active():
                    available_items = request_obj.item_type.get_lendable_items()
                    return HttpResponse(render_to_string("include/hardware_admin_lending.html", {
                            'items':available_items,
                            'request_id':request.POST['request_id']
                        }))
                return HttpResponse(render_to_string("<h1>Error: the request has expired</h1>"))

            if 'make_lending' in request.POST:
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




    def get_current_tabs(self):
        return hardware_tabs(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(HardwareAdminView, self).get_context_data(**kwargs)
        context['hw_list'] = ItemType.objects.all()
        return context