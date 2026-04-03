from app import hackathon_variables
from app.mixins import TabsViewMixin
from django.http import JsonResponse
from django.views.generic import TemplateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from user.mixins import IsHackerMixin

from hardware.models import ItemType, Borrowing, Request
from hardware.tables import BorrowingTable, BorrowingFilter
from hardware.views.admin import hardware_tabs


class HardwareBorrowingsView(IsHackerMixin, TabsViewMixin, SingleTableMixin, FilterView):
    template_name = 'hardware_borrowings.html'
    table_class = BorrowingTable
    table_pagination = {'per_page': 50}
    filterset_class = BorrowingFilter

    def get_context_data(self, **kwargs):
        context = super(HardwareBorrowingsView, self).get_context_data(**kwargs)
        if not self.request.user.is_hardware_admin:
            context['filter'] = False
            context['table'].exclude = ('id', 'user', 'lending_by', 'return_by')

        return context

    def get_current_tabs(self):
        return hardware_tabs(self.request.user)

    def get_queryset(self):
        if self.request.user.is_hardware_admin:
            return Borrowing.objects.all()
        else:
            return Borrowing.objects.get_queryset().filter(user=self.request.user)


class HardwareListView(IsHackerMixin, TabsViewMixin, TemplateView):
    template_name = 'hardware_list.html'

    def get_current_tabs(self):
        return hardware_tabs(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(HardwareListView, self).get_context_data(**kwargs)
        context['hw_list'] = ItemType.objects.all()
        requests = Request.objects.get_active_by_user(self.request.user)
        context['requests'] = {
            x.item_type.id: x.get_remaining_time() for x in requests
        }
        return context

    def req_item(self, request):
        item = ItemType.objects.get(id=request.POST['item_id'])
        if item.get_available_count() > 0:
            item.make_request(request.user)
            return JsonResponse({
                'ok': True,
                'minutes': hackathon_variables.HARDWARE_REQUEST_TIME
            })

        return JsonResponse({'msg': "ERROR: There are no items available"})

    def check_availability(self, request):
        item_ids = request.POST['item_ids[]']
        items = ItemType.objects.filter(id__in=item_ids)
        available_items = []
        for item in items:
            if item.get_available_count() > 0:
                available_items.append({
                    "id": item.id,
                    "name": item.name
                })

        return JsonResponse({
            'available_items': available_items
        })

    def post(self, request):
        if request.is_ajax:
            if 'req_item' in request.POST:
                return self.req_item(request)
            if 'check_availability' in request.POST:
                return self.check_availability(request)
