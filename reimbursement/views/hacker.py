from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

from app.utils import reverse, hacker_tabs
from app.views import TabsView
from reimbursement import forms, models
from user.mixins import IsHackerMixin


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
