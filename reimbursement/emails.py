from app import emails
from app.utils import reverse


def create_reimbursement_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail("mails/reimbursement", reimb.hacker.email, c)


def create_reject_receipt_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail(
        "mails/reject_receipt",
        reimb.hacker.email,
        c,
        from_email=reimb.reimbursed_by.email,
    )


def create_no_reimbursement_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail("mails/no_reimbursement", reimb.hacker.email, c)


def create_travel_tickets_upload_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail(
        "mails/travel_tickets_upload", reimb.hacker.email, c, action_required=True
    )


def create_ticket_accepted_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail("mails/ticket_accepted", reimb.hacker.email, c)


def create_devpost_upload_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail(
        "mails/devpost_upload", reimb.hacker.email, c, action_required=True
    )


def create_project_invalidated_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail("mails/project_invalidated", reimb.hacker.email, c)


def create_devpost_approved_email(reimb, request):
    app = reimb.hacker.application
    c = _get_context(app, reimb, request)
    return emails.render_mail("mails/devpost_approved", reimb.hacker.email, c)


def _get_context(app, reimb, request):
    from django.conf import settings

    confirm_url = reverse("confirm_app", kwargs={"id": app.uuid_str}, request=request)
    form_url = reverse("reimbursement_dashboard", request=request)
    cancel_url = reverse("cancel_app", kwargs={"id": app.uuid_str}, request=request)
    if not request:
        base_url = "https://" + settings.HACKATHON_DOMAIN
        confirm_url = base_url + confirm_url
        form_url = base_url + form_url
        cancel_url = base_url + cancel_url

    return {
        "app": app,
        "reimb": reimb,
        "confirm_url": str(confirm_url),
        "form_url": str(form_url),
        "cancel_url": str(cancel_url),
    }
