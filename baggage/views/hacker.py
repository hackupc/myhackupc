from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from app.mixins import TabsViewMixin
from baggage.models import Bag, BAG_ADDED
from baggage.tables import BaggageCurrentHackerTable, BaggageListFilter


def hacker_tabs(user):
    t = [('Baggage', reverse('baggage_currenthacker'), False)]
    return t


class BaggageCurrentHacker(LoginRequiredMixin, TabsViewMixin, SingleTableMixin, FilterView):
    template_name = 'baggage_currenthacker.html'
    table_class = BaggageCurrentHackerTable
    filterset_class = BaggageListFilter
    table_pagination = {'per_page': 100}

    def get_current_tabs(self):
        return hacker_tabs(self.request.user)

    def get_queryset(self):
        user = self.request.user
        return Bag.objects.filter(status=BAG_ADDED, owner=user)
