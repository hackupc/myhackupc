from django.conf import settings
from django.core import mail

from app import emails
from app.utils import reverse


# online_option can be Live, Online, Changed
def create_invite_email(application, request):
    c = {
        'name': application.user.get_full_name,
        'reimb': getattr(application.user, 'reimbursement', None),
        'confirm_url': str(reverse('dashboard', request=request)),
        'cancel_url': str(reverse('cancel_app', request=request, kwargs={'id': application.uuid_str})),
        'hybrid_option': 'Online' if getattr(application, 'online', False) else 'Live',
    }
    if application.user.is_hacker():
        return emails.render_mail('mails/invitation_hacker', application.user.email, c)

    # if application.user.is_mentor():
    #     return emails.render_mail('mails/invitation_mentor', application.user.email, c)
    # return emails.render_mail('mails/invitation_volunteer', application.user.email, c)


def create_confirmation_email(application, request):
    c = {
        'name': application.user.get_full_name,
        'token': application.uuid_str,
        'qr_url': 'https://quickchart.io/qr?size=350&text=%s'
                  % application.uuid_str,
        'cancel_url': str(reverse('cancel_app', request=request, kwargs={'id': application.uuid_str})),
        'is_hacker': application.user.is_hacker(),
        'is_sponsor': application.user.is_sponsor(),
    }
    if application.user.is_hacker():
        return emails.render_mail('mails/confirmation', application.user.email, c)


def create_lastreminder_email(application):
    c = {
        'name': application.user.get_full_name,
        'type': application.user.get_type_display(),
        # We need to make sure to redirect HTTP to HTTPS in production
        'confirm_url': 'http://%s%s' % (settings.HACKATHON_DOMAIN,
                                        reverse('confirm_app', kwargs={'id': application.uuid_str})),
        'cancel_url': 'http://%s%s' % (settings.HACKATHON_DOMAIN,
                                       reverse('cancel_app', kwargs={'id': application.uuid_str})),
        'is_hacker': application.user.is_hacker(),
        'is_sponsor': application.user.is_sponsor(),
    }
    if application.user.is_hacker():
        return emails.render_mail('mails/last_reminder', application.user.email, c, action_required=True)


def send_batch_emails(emails):
    connection = mail.get_connection()
    connection.send_messages(emails)
