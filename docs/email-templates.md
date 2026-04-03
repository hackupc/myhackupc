# Email Templates

myhackupc sends emails using Django's template system. Each email consists of two template files:
- `*_subject.txt` — the subject line (one line of text, no HTML)
- `*_message.html` — the email body (HTML)

---

## All Emails the System Sends

| Email | Sent when | App | Template path |
|---|---|---|---|
| Invitation - Hacker | User is invited as a hacker | applications | `applications/templates/mails/invitation_hacker_*` |
| Volunteer invitation | (sending code currently disabled) | applications | `applications/templates/mails/invitation_volunteer_*` |
| Mentor invitation | (sending code currently disabled) | applications | `applications/templates/mails/invitation_mentor_*` |
| Confirmation | Hacker confirms their attendance | applications | `applications/templates/mails/confirmation_*` |
| Last Reminder | Reminder before event starts | applications | `applications/templates/mails/last_reminder_*` |
| Reimbursement | Hacker is eligible for travel reimbursement | reimbursement | `reimbursement/templates/mails/reimbursement_*` |
| Reject Receipt | Submitted receipt is rejected | reimbursement | `reimbursement/templates/mails/reject_receipt_*` |
| No Reimbursement | Hacker is not eligible for reimbursement | reimbursement | `reimbursement/templates/mails/no_reimbursement_*` |
| Travel Tickets Upload | Hacker needs to upload travel tickets | reimbursement | `reimbursement/templates/mails/travel_tickets_upload_*` |
| Ticket Accepted | Travel ticket is accepted | reimbursement | `reimbursement/templates/mails/ticket_accepted_*` |
| Devpost Upload | Hacker needs to submit project to Devpost | reimbursement | `reimbursement/templates/mails/devpost_upload_*` |
| Project Invalidated | Submitted Devpost project is invalid | reimbursement | `reimbursement/templates/mails/project_invalidated_*` |
| Devpost Approved | Devpost project is approved | reimbursement | `reimbursement/templates/mails/devpost_approved_*` |
| Verify Email | User needs to verify their email address | user | `user/templates/mails/verify_email_*` |
| Password Reset | User requests password reset | user | `user/templates/mails/password_reset_*` |
| Sponsor Link | Admin shares sponsor signup link with user | user | `user/templates/mails/sponsor_link_*` |

Shared email components (footer, buttons, images) are in `app/templates/mails/include/`. App-specific includes also live alongside their templates: `applications/templates/mails/include/` and `reimbursement/templates/mails/include/`.

---

## How to Edit Email Content

1. Find the email in the table above
2. Open the `*_message.html` file — this is the email body
3. Edit the HTML content. You can use Django template tags (`{{ variable }}`, `{% if %}`, etc.)
4. To change the subject line, edit the `*_subject.txt` file

---

## Variables Available in Each Template

Each email has a set of variables passed to it from the Python code. Here is where those variables are defined:

| Email group | Python file | Context variables |
|---|---|---|
| Invite (hacker) | `applications/emails.py` → `create_invite_email` | `name`, `reimb`, `confirm_url`, `cancel_url`, `hybrid_option` |
| Confirmation | `applications/emails.py` → `create_confirmation_email` | `name`, `token`, `qr_url`, `cancel_url`, `is_hacker`, `is_sponsor` |
| Last reminder | `applications/emails.py` → `create_lastreminder_email` | `name`, `type`, `confirm_url`, `cancel_url`, `is_hacker`, `is_sponsor` |
| Reimbursement emails | `reimbursement/emails.py` | `app`, `reimb`, `confirm_url`, `form_url`, `cancel_url` |
| User emails | `user/emails.py` | `user`, `activate_url` (for verify email); `user`, `reset_url` (for password reset); `user`, `user_sponsor_url`, `app_sponsor_url`, `sponsor_name` (for sponsor link) |

---

## How to Add a New Variable to an Email

Example: you want to add `{{ deadline }}` to the hacker invitation email.

### Step 1: Find the Python function that creates the email

Open `applications/emails.py` and find `create_invite_email`. You will see a `c = { ... }` dictionary — this is the context passed to the template.

### Step 2: Add the variable to the context dict

```python
c = {
    'name': application.user.get_full_name,
    'reimb': getattr(application.user, 'reimbursement', None),
    'confirm_url': str(reverse('dashboard', request=request)),
    'cancel_url': str(reverse('cancel_app', request=request, kwargs={'id': application.uuid_str})),
    'hybrid_option': 'Online' if getattr(application, 'online', False) else 'Live',
    'deadline': settings.HACKATHON_END,   # ← add your variable here
}
```

### Step 3: Use the variable in the template

Open `applications/templates/mails/invitation_hacker_message.html` and add:

```html
<p>The deadline to confirm is {{ deadline }}.</p>
```

### Step 4: Verify

Trigger the email in local dev (or use the Django shell) and confirm the variable renders correctly.
