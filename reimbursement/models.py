# coding=utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from reimbursement import emails
from user.models import User

DEFAULT_EXPIRY_DATE = settings.REIMBURSEMENT_EXPIRY_DATE

RE_WAITLISTED = "W"
RE_PEND_TICKET = "PT"
RE_PEND_APPROVAL = "PA"
RE_APPROVED = "A"
RE_PEND_DEMO_VAL = "PD"
RE_FINALIZED = "F"
RE_EXPIRED = "X"
RE_FRIEND_SUBMISSION = "FS"

RE_STATUS = [
    (RE_WAITLISTED, "Wait listed"),
    (RE_PEND_TICKET, "Pending receipt submission"),
    (RE_PEND_APPROVAL, "Pending receipt approval"),
    (RE_APPROVED, "Receipt approved"),
    (RE_EXPIRED, "Expired"),
    (RE_FRIEND_SUBMISSION, "Friend submission"),
    (RE_FINALIZED, "Reimbursement Approved"),
    (RE_PEND_DEMO_VAL, "Pending demo validation"),
]


def check_friend_emails(friend_emails, user_email):
    emails = friend_emails.replace(" ", "").split(",")
    if user_email in emails:
        raise Exception("%s is your own email" % user_email)
    for email in emails:
        try:
            user = User.objects.get(email=email)
        except Exception:
            raise Exception("%s is not a registered hacker" % email)

        try:
            if user.reimbursement.waitlisted():
                raise Exception("%s has a waitlisted reimbursement" % email)
            if user.reimbursement.expired:
                raise Exception("%s reimbursement is expired" % email)
            if user.reimbursement.is_draft():
                raise Exception("%s reimbursement is still under revision" % email)
            if user.reimbursement.status == RE_APPROVED:
                raise Exception("%s already has an accepted reimbursement" % email)
            if user.reimbursement.status == RE_FRIEND_SUBMISSION:
                raise Exception("%s already has an accepted reimbursement" % email)

        except Reimbursement.DoesNotExist:
            raise Exception("%s didn't ask for reimbursement" % email)


class Reimbursement(models.Model):
    # Admin controlled
    assigned_money = models.FloatField(default=0)
    reimbursement_money = models.FloatField(null=True, blank=True)
    public_comment = models.CharField(max_length=300, null=True, blank=True)

    devpost = models.URLField(blank=True, null=True, default="")

    # User controlled
    paypal_email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=300, null=True, blank=True)
    venmo_user = models.CharField(max_length=40, null=True, blank=True)
    receipt = models.FileField(
        null=True,
        blank=True,
        upload_to="receipt",
    )
    multiple_hackers = models.BooleanField(default=False)
    friend_emails = models.CharField(null=True, blank=True, max_length=400)
    origin = models.CharField(max_length=300)

    # If a friend submitted receipt
    friend_submission = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="friend_submissions",
        null=True,
        blank=True,
    )

    # Meta
    hacker = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    reimbursed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="reimbursements_made",
        on_delete=models.SET_NULL,
    )
    expiration_time = models.DateTimeField(default=settings.REIMBURSEMENT_EXPIRY_DATE)
    update_time = models.DateTimeField(default=timezone.now)
    creation_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=2, choices=RE_STATUS, default=RE_PEND_TICKET)

    @property
    def max_assignable_money(self):
        return self.assigned_money

    @property
    def friend_emails_list(self):
        if not self.multiple_hackers:
            return None
        return (self.friend_emails or "").replace(" ", "").split(",")

    @property
    def timeleft_expiration(self):
        if not self.expiration_time:
            return None
        return self.expiration_time - timezone.now()

    @property
    def expired(self):
        return self.status == RE_EXPIRED

    def generate_draft(self, application):
        if self.status != RE_PEND_TICKET:
            return
        self.origin = application.origin
        if not application.reimb_amount:
            self.assigned_money = 0
        else:
            self.assigned_money = application.reimb_amount
        self.hacker = application.user
        self.save()

    def expire(self):
        self.status = RE_EXPIRED
        self.save()

    def send(self, user):
        if not self.assigned_money:
            raise ValidationError(
                "Reimbursement can't be sent because " "there's no assigned money"
            )
        if self.status == RE_PEND_TICKET:
            self.status = RE_PEND_TICKET
            self.status_update_date = timezone.now()
            self.reimbursed_by = user
            self.reimbursement_money = None
            self.expiration_time = DEFAULT_EXPIRY_DATE
            self.save()

    def validate(self, user):
        if self.status == RE_PEND_DEMO_VAL:
            self.status = RE_FINALIZED
            self.status_update_date = timezone.now()
            self.reimbursed_by = user
            self.save()

    def invalidate(self, user):
        if self.status == RE_PEND_DEMO_VAL:
            self.status = RE_WAITLISTED
            self.status_update_date = timezone.now()
            self.reimbursed_by = user
            self.save()

    def no_reimb(self, user):
        if self.status == RE_PEND_TICKET:
            self.status = RE_WAITLISTED
            self.status_update_date = timezone.now()
            self.reimbursed_by = user
            self.reimbursement_money = 0
            self.assigned_money = 0
            self.save()

    def is_sent(self):
        return self.status in [RE_PEND_APPROVAL, RE_PEND_TICKET]

    def has_friend_submitted(self):
        return self.status == RE_FRIEND_SUBMISSION

    def is_draft(self):
        return self.status == RE_PEND_TICKET

    def is_accepted(self):
        return self.status in RE_APPROVED

    def is_finalized(self):
        return self.status == RE_FINALIZED

    def is_pending_demo_validation(self):
        return self.status == RE_PEND_DEMO_VAL

    def waitlisted(self):
        return self.status == RE_WAITLISTED

    def needs_action(self):
        return self.can_submit_receipt()

    def can_submit_receipt(self):
        return (
            self.status == RE_PEND_TICKET
            and not self.expired
            and not self.hacker.application.is_rejected()
        )

    def reject_receipt(self, user, request):
        self.expiration_time = DEFAULT_EXPIRY_DATE
        self.status = RE_PEND_TICKET
        self.reimbursed_by = user
        self.reimbursement_money = None
        self.receipt.delete()
        if self.multiple_hackers:
            for reimb in self.friend_submissions.all():
                reimb.friend_submission = None
                reimb.reimbursement_money = None
                reimb.expiration_time = DEFAULT_EXPIRY_DATE
                reimb.public_comment = (
                    "Your friend %s submission has not been accepted"
                    % self.hacker.get_full_name()
                )
                reimb.status = RE_PEND_TICKET
                reimb.save()
        return emails.create_reject_receipt_email(self, request)

    def accept_receipt(self, user):
        self.status = RE_APPROVED
        self.reimbursed_by = user

    def submit_receipt(self):
        self.status = RE_PEND_APPROVAL
        self.public_comment = None
        self.friend_submission = None
        self.reimbursement_money = None
        if self.multiple_hackers:
            for reimb in Reimbursement.objects.filter(
                hacker__email__in=self.friend_emails_list
            ):
                reimb.friend_submission = self
                reimb.status = RE_FRIEND_SUBMISSION
                reimb.public_comment = None
                reimb.save()

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.update_time = timezone.now()
        super(Reimbursement, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
