# Create your views here.
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Avg, F, Q, CharField
from django.db.models.functions import Concat
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django_tables2 import SingleTableMixin
from django.utils import timezone

from app.mixins import TabsViewMixin
from applications import emails
from applications.emails import send_batch_emails
from applications.models import (
    APP_PENDING,
    APP_DUBIOUS,
    APP_BLACKLISTED,
    APP_INVITED,
    APP_LAST_REMIDER,
    APP_CONFIRMED,
    APP_REJECTED,
)
from organizers import models
from organizers.tables import AdminTeamListTable
from user.mixins import IsDirectorMixin

from organizers.views.lists import hacker_tabs


class InviteTeamListView(
    TabsViewMixin, IsDirectorMixin, SingleTableMixin, TemplateView
):
    template_name = "invite_list.html"
    table_class = AdminTeamListTable
    table_pagination = {"per_page": 100}

    def get_current_tabs(self):
        return hacker_tabs(self.request.user)

    def get_queryset(self):
        hackersList = (
            models.HackerApplication.objects.filter(
                status__in=[
                    APP_PENDING,
                    APP_CONFIRMED,
                    APP_LAST_REMIDER,
                    APP_INVITED,
                    APP_REJECTED,
                ]
            )
            .exclude(user__team__team_code__isnull=True)
            .values("user__team__team_code")
            .annotate(
                vote_avg=Avg("vote__calculated_vote"),
                members=Count("user", distinct=True),
                invited=Count(
                    Concat("status", "user__id", output_field=CharField()),
                    filter=Q(status__in=[APP_INVITED, APP_LAST_REMIDER]),
                    distinct=True,
                ),
                accepted=Count(
                    Concat("status", "user__id", output_field=CharField()),
                    filter=Q(status=APP_CONFIRMED),
                    distinct=True,
                ),
                live_pending=Count(
                    Concat("status", "user__id", output_field=CharField()),
                    filter=Q(status__in=[APP_PENDING, APP_REJECTED], online=False),
                    distinct=True,
                ),
            )
            .exclude(members=F("accepted"))
            .exclude(Q(live_pending=0) | Q(live_pending__gt=F("members") / 2))
            .order_by("-vote_avg")
        )

        return hackersList

    def get_context_data(self, **kwargs):
        context = super(InviteTeamListView, self).get_context_data(**kwargs)
        context.update({"teams": True})

        n_live_hackers = models.HackerApplication.objects.filter(
            status__in=[APP_INVITED, APP_LAST_REMIDER, APP_CONFIRMED], online=False
        ).count()

        n_invited_hackers_today = models.HackerApplication.objects.filter(
            status__in=[APP_INVITED],
            online=False,
            status_update_date__date=timezone.now().date(),
        ).count()

        n_waitlisted_hackers = models.HackerApplication.objects.filter(
            status__in=[APP_REJECTED], online=False
        ).count()

        context.update(
            {
                "n_live_hackers": n_live_hackers,
                "n_live_per_hackers": n_live_hackers
                * 100
                / getattr(settings, "N_MAX_LIVE_HACKERS", 0),
                "n_invited_hackers_today": n_invited_hackers_today,
                "n_waitlisted_hackers": n_waitlisted_hackers,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("selected")
        apps = (
            models.HackerApplication.objects.filter(user__team__team_code__in=ids)
            .exclude(status__in=[APP_DUBIOUS, APP_BLACKLISTED])
            .annotate(count=Count("vote"))
            .filter(count__gte=5)
        )
        mails = []
        errors = 0
        for app in apps:
            try:
                app.invite(
                    request.user,
                    online=request.POST.get("force_online", "false") == "true",
                )
                m = emails.create_invite_email(app, request)
                mails.append(m)
            except ValidationError:
                errors += 1
        if mails:
            send_batch_emails(mails)
            messages.success(request, "%s applications invited" % len(mails))
        else:
            errorMsg = "No applications invited"
            if errors != 0:
                errorMsg = "%s applications not invited" % errors
            messages.error(request, errorMsg)

        return HttpResponseRedirect(reverse("invite_teams_list"))
