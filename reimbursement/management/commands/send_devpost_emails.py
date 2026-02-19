from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from reimbursement.models import Reimbursement, RE_APPROVED
from reimbursement import emails


class Command(BaseCommand):
    help = 'Sends automatic emails to upload Devpost link to approved reimbursements'

    def handle(self, *args, **options):
        # Check if the event has ended
        if timezone.now() < settings.HACKATHON_EVENT_END:
            self.stdout.write(self.style.WARNING('Event has not ended yet. Skipping Devpost emails.'))
            return

        # We target reimbursements that have the receipt approved (RE_APPROVED),
        # hasn't uploaded a devpost link yet (devpost=''),
        # and we haven't sent the reminder email yet (devpost_email_sent=False).
        reimbursements = Reimbursement.objects.filter(
            status=RE_APPROVED,
            devpost='',
            devpost_email_sent=False
        )

        self.stdout.write(f'Found {reimbursements.count()} reimbursements pending Devpost link.')
 
        sent_count = 0
        for reimb in reimbursements:
            try:
                msg = emails.create_devpost_upload_email(reimb, None)
                msg.send()
                reimb.devpost_email_sent = True
                reimb.save()
                sent_count += 1
            except Exception as e:
                self.stderr.write(f'Error sending email to {reimb.hacker.email}: {str(e)}')

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {sent_count} emails.'))
