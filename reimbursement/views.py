from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from app.mixins import TabsViewMixin
from app.utils import reverse, hacker_tabs
from app.views import TabsView
from applications import models as app_mod
from applications.emails import send_batch_emails
from reimbursement import forms, models, emails
from reimbursement.tables import (
    ReimbursementTable,
    ReimbursementFilter,
    SendReimbursementTable,
    SendReimbursementFilter,
)
from user.mixins import IsOrganizerMixin, IsDirectorMixin, IsHackerMixin
from organizers.views import hacker_tabs as organizer_tabs


class ReimbursementHacker(IsHackerMixin, TabsView):
    template_name = "reimbursement_hacker.html"

    def get_current_tabs(self):
        return hacker_tabs(self.request.user)

    def get_context_data(self, **kwargs):
        c = super(ReimbursementHacker, self).get_context_data(**kwargs)
        reimb = getattr(self.request.user, "reimbursement", None)
        if not reimb:
            raise Http404
        c.update(
            {
                "form": forms.ReceiptSubmissionReceipt(
                    instance=self.request.user.reimbursement
                )
            }
        )
        return c

    def post(self, request, *args, **kwargs):
        # check reimbursment status and act accordingly
        # if status is pending demo link, then validate the devpost link
        # if status is pending receipt, then validate the receipt
        if request.user.reimbursement.status == models.RE_PEND_TICKET:
            try:
                form = forms.ReceiptSubmissionReceipt(
                    request.POST, request.FILES, instance=request.user.reimbursement
                )
            except Exception:
                form = forms.ReceiptSubmissionReceipt(request.POST, request.FILES)
            if form.is_valid():
                reimb = form.save(commit=False)
                reimb.hacker = request.user
                # set status to pending demo link
                reimb.status = models.RE_PEND_APPROVAL
                reimb.save()
                messages.success(
                    request,
                    "We have now received your reimbursement. "
                    "Processing will take some time, so please be patient.",
                )
                return HttpResponseRedirect(reverse("reimbursement_dashboard"))
            else:
                c = self.get_context_data()
                c.update({"form": form})
                return render(request, self.template_name, c)
        else:
            try:
                form = forms.DevpostValidationForm(
                    request.POST, instance=request.user.reimbursement
                )
            except Exception:
                form = forms.DevpostValidationForm(request.POST)
            if form.is_valid():
                print("valid")
                reimb = form.save(commit=False)
                reimb.devpost = form.cleaned_data.get("devpost")
                reimb.status = models.RE_PEND_DEMO_VAL
                reimb.save()
                messages.success(
                    request,
                    "We have now received your demo link. "
                    "Processing will take some time, so please be patient.",
                )

                return HttpResponseRedirect(reverse("reimbursement_dashboard"))
            else:
                print(form.errors)
                print("invalid")
                c = self.get_context_data()
                c.update({"form": form})
                return render(request, self.template_name, c)


class ReimbursementDetail(IsOrganizerMixin, TabsView):
    template_name = "reimbursement_detail.html"

    def get_current_tabs(self):
        return None

    def get_back_url(self):
        return reverse("reimbursement_list")

    def get_context_data(self, **kwargs):
        c = super(ReimbursementDetail, self).get_context_data(**kwargs)
        id_ = kwargs.get("id", None)
        if not id_:
            return c
        reimb = get_object_or_404(models.Reimbursement, pk=id_)
        c.update(
            {
                "reimb": reimb,
                "edit_form": forms.EditReimbursementForm(instance=reimb),
                "reject_form": forms.RejectReceiptForm(instance=reimb),
                "review": True,
                "accept_form": forms.AcceptReceiptForm(instance=reimb),
            }
        )
        return c

    def post(self, request, *args, **kwargs):
        if "edit" in request.POST:
            id_ = kwargs.get("id", None)
            reimb = models.Reimbursement.objects.get(pk=id_)
            form = forms.EditReimbursementForm(request.POST, instance=reimb)

            if form.is_valid():
                form.save()
                messages.success(
                    self.request, "Changes in reimbursement successfully saved!"
                )
            else:
                return render(
                    request, self.template_name, {"reimb": reimb, "edit_form": form}
                )
        elif "validate" in request.POST:
            id_ = kwargs.get("id", None)
            reimb = models.Reimbursement.objects.get(pk=id_)
            form = forms.ValidateReimbursementForm(request.POST, instance=reimb)
            print(form)
            if form.is_valid():
                form.save(commit=False)
                reimb.validate(request.user)
                form.save()
                messages.success(self.request, "Reimbursement successfully validated!")
            else:
                return render(
                    request, self.template_name, {"reimb": reimb, "validate_form": form}
                )
        elif "reject" in request.POST:
            id_ = kwargs.get("id", None)
            reimb = models.Reimbursement.objects.get(pk=id_)
            form = forms.RejectReceiptForm(request.POST, instance=reimb)
            if form.is_valid():
                form.save(commit=False)
                m = form.instance.reject_receipt(request.user, request)
                m.send()
                form.save()
                messages.success(request, "Receipt rejected")
            else:
                a_form = forms.AcceptReceiptForm(instance=reimb)
                r_form = forms.RejectReceiptForm(instance=reimb)
                c = self.get_context_data()
                c.update({"reject_form": r_form, "accept_form": a_form})
                return render(request, self.template_name, c)
        elif "invalidate" in request.POST:
            id_ = kwargs.get("id", None)
            reimb = models.Reimbursement.objects.get(pk=id_)
            reimb.invalidate(request.user)
            messages.success(request, "Reimbursement invalidated")
        else:
            id_ = request.POST.get("id", None)
            reimb = models.Reimbursement.objects.get(pk=id_)
            a_form = forms.AcceptReceiptForm(instance=reimb)
            r_form = forms.RejectReceiptForm(instance=reimb)

            if request.POST.get("accept", None):
                a_form = forms.AcceptReceiptForm(request.POST, instance=reimb)
                if a_form.is_valid():
                    a_form.save(commit=False)
                    a_form.instance.accept_receipt(request.user)
                    a_form.save()
                    messages.success(request, "Receipt accepted")
                else:
                    c = self.get_context_data()
                    c.update({"reject_form": r_form, "accept_form": a_form})
                    return render(request, self.template_name, c)

            elif request.POST.get("reject", None):
                r_form = forms.RejectReceiptForm(request.POST, instance=reimb)
                if r_form.is_valid():
                    r_form.save(commit=False)
                    m = r_form.instance.reject_receipt(request.user, request)
                    m.send()
                    r_form.save()
                    messages.success(request, "Receipt rejected")
                else:
                    c = self.get_context_data()
                    c.update({"reject_form": r_form, "accept_form": a_form})
                    return render(request, self.template_name, c)

        return HttpResponseRedirect(
            reverse("reimbursement_detail", kwargs={"id": reimb.pk})
        )


class ReceiptReview(ReimbursementDetail):
    def get_current_tabs(self):
        return organizer_tabs(self.request.user)

    def get_back_url(self):
        return None

    def get_context_data(self, **kwargs):
        c = super(ReceiptReview, self).get_context_data(**kwargs)
        reimb = (
            models.Reimbursement.objects.filter(status=models.RE_PEND_APPROVAL)
            .order_by("-update_time")
            .first()
        )
        c.update(
            {
                "reimb": reimb,
                "reject_form": forms.RejectReceiptForm(instance=reimb),
                "review": True,
                "accept_form": forms.AcceptReceiptForm(instance=reimb),
                "back_url": reverse("receipt_review"),
                "edit_form": forms.EditReimbursementForm(instance=reimb),
                "form": forms.ReceiptSubmissionReceipt(instance=reimb)
            }
        )
        return c

    def post(self, request, *args, **kwargs):
        id_ = request.POST.get("id", None)
        reimb = models.Reimbursement.objects.get(pk=id_)
        a_form = forms.AcceptReceiptForm(instance=reimb)
        r_form = forms.RejectReceiptForm(instance=reimb)
        e_form = forms.EditReimbursementForm(instance=reimb)

        if request.POST.get("accept", None):
            a_form = forms.AcceptReceiptForm(request.POST, instance=reimb)
            if a_form.is_valid():
                a_form.save(commit=False)
                a_form.instance.accept_receipt(request.user)
                a_form.save()
                messages.success(request, "Receipt accepted")
            else:
                c = self.get_context_data()
                c.update({"reject_form": r_form, "accept_form": a_form})
                return render(request, self.template_name, c)

        elif request.POST.get("reject", None):
            r_form = forms.RejectReceiptForm(request.POST, instance=reimb)
            if r_form.is_valid():
                r_form.save(commit=False)
                m = r_form.instance.reject_receipt(request.user, request)
                m.send()
                r_form.save()
                messages.success(request, "Receipt rejected")
            else:
                c = self.get_context_data()
                c.update({"reject_form": r_form, "accept_form": a_form})
                return render(request, self.template_name, c)

        elif request.POST.get("edit", None):
            e_form = forms.EditReimbursementForm(request.POST, instance=reimb)
            if e_form.is_valid():
                e_form.save()
                messages.success(
                    self.request, "Changes in reimbursement successfully saved!"
                )
            else:
                c = self.get_context_data()
                c.update({"reimb": reimb, "edit_form": e_form})
                return render(request, self.template_name, c)

        return HttpResponseRedirect(reverse("receipt_review"))


class ReimbursementListView(
    IsOrganizerMixin, TabsViewMixin, SingleTableMixin, FilterView
):
    template_name = "reimbursements_table.html"
    table_class = ReimbursementTable
    filterset_class = ReimbursementFilter
    table_pagination = {"per_page": 100}

    def get_current_tabs(self):
        return organizer_tabs(self.request.user)

    def get_queryset(self):
        return models.Reimbursement.objects.all()


class SendReimbursementListView(
    IsDirectorMixin, TabsViewMixin, SingleTableMixin, FilterView
):
    template_name = "reimbursement_send_table.html"
    table_class = SendReimbursementTable
    filterset_class = SendReimbursementFilter
    table_pagination = {"per_page": 100}

    def get_current_tabs(self):
        return organizer_tabs(self.request.user)

    def get_queryset(self):
        status = [
            app_mod.APP_INVITED,
            app_mod.APP_LAST_REMIDER,
            app_mod.APP_CONFIRMED,
            app_mod.APP_ATTENDED,
        ]
        return (
            models.Reimbursement.objects.filter(status=models.RE_DRAFT)
            .filter(hacker__hackerapplication_application__status__in=status)
            .all()
        )

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("selected")
        no_reimb = request.POST.get("no_reimb", False)
        reimbs = models.Reimbursement.objects.filter(pk__in=ids).all()
        mails = []
        errors = 0
        for reimb in reimbs:
            try:

                if not no_reimb:
                    assigned_money = request.POST.get("am_" + str(reimb.pk))
                    reimb.assigned_money = assigned_money
                    reimb.send(request.user)
                    m = emails.create_reimbursement_email(reimb, request)
                else:
                    reimb.no_reimb(request.user)
                    m = emails.create_no_reimbursement_email(reimb, request)
                mails.append(m)
            except ValidationError:
                errors += 1

        if mails:
            send_batch_emails(mails)
            if no_reimb:
                msg = "%s no reimbursements message sent"
            else:
                msg = "%s reimbursements sent"
            messages.success(request, msg % len(mails))
        else:
            messages.error(request, "%s reimbursements not sent" % errors)

        return HttpResponseRedirect(reverse("send_reimbursement"))
