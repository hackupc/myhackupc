from django.contrib import messages
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import render
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.views.generic import TemplateView

from applications import models, forms
from organizers.tables import SponsorFilter, SponsorListTableWithNoAction
from organizers.views import _OtherApplicationsListView
from user.mixins import IsSponsorMixin
from user import models as userModels


class SponsorApplicationView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(SponsorApplicationView, self).get_context_data(**kwargs)
        form = forms.SponsorForm()
        context.update({"form": form, "is_sponsor": True})
        try:
            uid = force_text(urlsafe_base64_decode(self.kwargs.get("uid", None)))
            user = userModels.User.objects.get(pk=uid)
            context.update({"user": user})
            context.update({"company_name": user.name})
        except (TypeError, ValueError, OverflowError, userModels.User.DoesNotExist):
            pass

        return context

    def get(self, request, *args, **kwargs):
        try:
            uid = force_text(urlsafe_base64_decode(self.kwargs.get("uid", None)))
            user = userModels.User.objects.get(pk=uid)
            real_token = userModels.Token.objects.get(pk=user).uuid_str()
            token = self.kwargs.get("token", None)
        except (
            TypeError,
            ValueError,
            OverflowError,
            userModels.User.DoesNotExist,
            userModels.Token.DoesNotExist,
        ):
            raise Http404("Invalid url")
        if token != real_token:
            raise Http404("Invalid url")
        if not user.has_applications_left()[0]:
            raise Http404("You have no applications left")
        return super(SponsorApplicationView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = forms.SponsorForm(request.POST, request.FILES)
        try:
            uid = force_text(urlsafe_base64_decode(self.kwargs.get("uid", None)))
            user = userModels.User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, userModels.User.DoesNotExist):
            return Http404("How did you get here?")
        has_applications_left, applied = user.has_applications_left()
        if not has_applications_left:
            form.add_error(None, "You have no applications left")
        elif form.is_valid():
            name = form.cleaned_data["name"]
            app = models.SponsorApplication.objects.filter(user=user, name=name).first()
            if app:
                form.add_error("name", "This name is already taken. Have you applied?")
            else:
                user.pk = None
                user.max_applications = 0
                application = form.save(commit=False)
                user.password = ""
                error = True
                while error:
                    user.email = ("+%s@" % applied).join(user.email.split("@"))
                    try:
                        user.save()
                        error = False
                    except IntegrityError:
                        applied += 1
                application.user = user
                application.save()
                messages.success(request, "We have now received your application. ")
                return render(request, "sponsor_submitted.html")
        c = self.get_context_data()
        c.update({"form": form})
        return render(request, self.template_name, c)


class SponsorDashboard(IsSponsorMixin, _OtherApplicationsListView):
    table_class = SponsorListTableWithNoAction
    filterset_class = SponsorFilter

    def get_current_tabs(self):
        return None

    def get_queryset(self):
        return models.SponsorApplication.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(SponsorDashboard, self).get_context_data(**kwargs)
        context["otherApplication"] = True
        context["emailCopy"] = False
        return context
