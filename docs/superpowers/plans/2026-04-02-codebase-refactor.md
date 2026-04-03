# Codebase Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the myhackupc Django codebase so that new volunteer developers can navigate it, find what they need to change, and make changes confidently without breaking things.

**Architecture:** Split large `views.py` files into `views/` packages (one file per concern), push app-specific CSS out of global files into each app's `static/` folder, split the minified Bootstrap CSS into readable component files, and create a `docs/` folder with onboarding and how-to guides.

**Tech Stack:** Django 3.2, Python 3.10, Bootstrap 3, WhiteNoise for static files, SendGrid for email.

**Spec:** `docs/superpowers/specs/2026-04-02-codebase-refactor-design.md`

---

## Important: How to Verify After Each Task

This refactor does not add new behavior — every change is structural. There are no unit tests to run. Instead, use these verification steps after every task:

- **Dev server check:** `python manage.py runserver` — should start with no import errors
- **Management command check** (only after Task 9): `python manage.py expire_applications --help`
- **CSS visual check:** Load the app in a browser and verify the page looks correct
- **Import grep:** After splitting a views file, run `grep -r "from <app>.views" . --include="*.py"` to confirm all callers still resolve

---

## Phase 1: Documentation

---

### Task 1: Create `docs/getting-started.md`

**Files:**
- Create: `docs/getting-started.md`

- [ ] **Step 1: Create the file with this content**

```markdown
# Getting Started

myhackupc is the registration and event management tool for HackUPC. It is a Django web application used by three groups:

- **Hackers** — apply, confirm attendance, request travel reimbursement
- **Organizers** — review applications, vote, send invites, manage check-in, hardware, meals, baggage
- **Volunteers/Mentors** — access check-in and their own application flow

---

## Codebase Structure

The project is a standard Django multi-app repository. Each feature lives in its own app folder. Here is what each active app does:

| App | Purpose |
|---|---|
| `app/` | Core config: settings, base templates, global CSS, shared utilities, hackathon variables |
| `applications/` | Hacker, volunteer, mentor, and sponsor application forms and status flow |
| `organizers/` | Application review, voting, batch invites, waitlist/blacklist management |
| `user/` | Authentication: sign up, login, password reset, email verification, user roles |
| `reimbursement/` | Travel reimbursement requests, receipt upload, organizer approval flow |
| `checkin/` | QR-code-based event check-in for hackers, volunteers, and mentors |
| `baggage/` | Baggage drop-off and pick-up tracking |
| `hardware/` | Hardware lab lending requests |
| `meals/` | Meal distribution tracking per hacker |
| `teams/` | Team formation and membership |
| `stats/` | Organizer-facing analytics dashboards |

Excluded from active development: `judging`, `offer`, `discord`.

---

## Where Things Live

### Templates
Each app has its own `templates/` folder. For example:
- Hacker application form: `applications/templates/`
- Organizer review interface: `organizers/templates/`
- Email templates: `<app>/templates/mails/` in the relevant app

### Styles
- Global layout, typography, theme colors: `app/static/css/main.css`
- Bootstrap component overrides: `app/static/css/bootstrap-overrides/` (one file per component)
- App-specific styles: `<app>/static/css/<app>.css` (e.g. `baggage/static/css/baggage.css`)

### URLs
| URL prefix | App |
|---|---|
| `/` | `applications` (hacker dashboard) |
| `/applications/` | `organizers` (review interface) |
| `/user/` | `user` (auth) |
| `/reimbursement/` | `reimbursement` |
| `/checkin/` | `checkin` |
| `/baggage/` | `baggage` |
| `/hardware/` | `hardware` |
| `/meals/` | `meals` |
| `/teams/` | `teams` |
| `/stats/` | `stats` |
| `/admin/` | Django admin |

---

## The Most Important Config File

**`app/hackathon_variables.py`** — this is what you touch every year. It contains:
- Application open/close deadlines
- Reimbursement cap amounts
- Feature flags (baggage, hardware, reimbursement, discord)
- Hackathon name, domain, email addresses
- Slack channel IDs

A template with all available variables is at `app/hackathon_variables.py.template`.

---

## Next Steps

- **Set up your local environment:** see `docs/setting-up.md`
- **Make a change:** see `docs/contributing.md`
- **Edit an email template:** see `docs/email-templates.md`
```

- [ ] **Step 2: Verify the file was created**

```bash
ls docs/
```

---

### Task 2: Create `docs/setting-up.md` and update README

**Files:**
- Create: `docs/setting-up.md`
- Modify: `README.md` (add pointer to docs at the top of the Setup section)

- [ ] **Step 1: Create `docs/setting-up.md`**

Extract the setup instructions from `README.md` (the "Setup", "Available environment variables", "Server > Local environment", and "Dummy data" sections) and write them here in a single cohesive guide. Use this structure:

```markdown
# Setting Up myhackupc Locally

## Prerequisites

- Python 3.10
- `virtualenv`

---

## Installation

```bash
git clone https://github.com/hackupc/myhackupc && cd myhackupc
virtualenv env --python=python3.10
source ./env/bin/activate
pip install -r requirements.txt
```

> **Note on psycopg2-binary:** If you get an error, install openssl@3 and export LDFLAGS, CPPFLAGS, and PKG_CONFIG_PATH before running pip install.

---

## Configuration

Copy the hackathon variables template and fill in the values:

```bash
cp app/hackathon_variables.py.template app/hackathon_variables.py
```

Open `app/hackathon_variables.py` and set at minimum:
- `HACKATHON_NAME`
- `HACKATHON_DOMAIN` (use `localhost:8000` for local dev)
- Application deadlines

---

## Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Running the Dev Server

```bash
source ./env/bin/activate
python manage.py runserver
```

Visit http://localhost:8000. Log in with the superuser you created.

---

## Environment Variables (Optional)

| Variable | Purpose |
|---|---|
| `SG_KEY` | SendGrid API key. If not set, emails are written to the filesystem at `sent_emails/` |
| `PROD_MODE` | Disables Django debug mode |
| `SECRET` | Web app secret key |
| `DATABASE_URL` | Database connection URL. Defaults to SQLite |
| `SL_TOKEN` | Slack token for automatic invites on confirmation |
| `DROPBOX_OAUTH2_TOKEN` | Enables Dropbox as file storage backend |
| `MLH_CLIENT_SECRET` | Enables MyMLH sign-up (`app_id@secret` format) |
| `CAS_SERVER` | Enables CAS login for other platforms |

See `README.md` for the full list and Heroku/production deployment instructions.

---

## Verifying Your Changes

After making code changes:

1. Restart the dev server (`Ctrl+C`, then `python manage.py runserver`)
2. Navigate to the affected page in the browser
3. If you changed a model, run `python manage.py makemigrations && python manage.py migrate`
4. If you changed CSS, hard-refresh the browser (Ctrl+Shift+R / Cmd+Shift+R)
```

- [ ] **Step 2: Add a pointer to `docs/` at the top of the Setup section in `README.md`**

Find the `## Setup` heading in `README.md` and add this line immediately after it:

```markdown
> For a step-by-step guide see [docs/setting-up.md](docs/setting-up.md). For codebase orientation see [docs/getting-started.md](docs/getting-started.md).
```

- [ ] **Step 3: Verify dev server still starts**

```bash
python manage.py runserver
```

Expected: starts without errors.

---

### Task 3: Create `docs/contributing.md`

**Files:**
- Create: `docs/contributing.md`

- [ ] **Step 1: Create the file with this content**

```markdown
# Contributing — Common Changes

This document walks through the most common yearly changes with exact file paths.

---

## Example 1: Adding or Removing a Field from the Hacker Application

The hacker application form is split across three layers: model, form, and template.

### 1. Update the model

File: `applications/models/hacker.py`

Add or remove the field from the `HackerApplication` model class. Use standard Django field types. Example:

```python
# Adding a new field
dietary_restrictions = models.CharField(
    max_length=200,
    blank=True,
    help_text="Any dietary restrictions we should know about?"
)
```

### 2. Create and run a migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Update the form

File: `applications/forms/hacker.py`

Add the field name to the `fields` list in `HackerApplicationForm.Meta`, and optionally customize its widget or label in the `widgets` or `labels` dicts.

### 4. Update the template

File: `applications/templates/include/application_form.html` (or the relevant template — look for the `{% for field in form %}` loop or the specific field rendering)

If you need custom layout for the new field, add it explicitly. Otherwise it will be rendered automatically by the form loop.

### 5. Verify

Start the dev server, go to the hacker application form, and confirm the new field appears.

---

## Example 2: Adding or Removing a Field from the Volunteer or Mentor Application

Same pattern as the hacker application, different files:

| Layer | Volunteer | Mentor |
|---|---|---|
| Model | `applications/models/volunteer.py` | `applications/models/mentor.py` |
| Form | `applications/forms/volunteer.py` | `applications/forms/mentor.py` |
| Template | `applications/templates/` (look for volunteer/mentor form template) | same |

Run `python manage.py makemigrations && python manage.py migrate` after changing the model.

---

## Example 3: Changing the Travel Reimbursement Cap

File: `app/hackathon_variables.py`

Find and update the reimbursement limit variables. No migration or code change needed — these are config values read at runtime.

---

## Where to Look for Other Things

| What you want to change | Where to look |
|---|---|
| Application status flow (pending → invited → confirmed) | `applications/models/base.py` |
| Who can review applications and vote | `organizers/views/review.py` |
| Batch invite algorithm | `organizers/views/batch_ops.py` |
| Email content | See `docs/email-templates.md` |
| Check-in logic | `checkin/views.py` |
| User roles and permissions | `user/models.py`, `user/mixins.py` |
| Hackathon name, dates, deadlines | `app/hackathon_variables.py` |
| Global styles | `app/static/css/main.css` |
| Bootstrap component styles | `app/static/css/bootstrap-overrides/` |
```

---

### Task 4: Create `docs/email-templates.md`

**Files:**
- Create: `docs/email-templates.md`

- [ ] **Step 1: Create the file with this content**

````markdown
# Email Templates

myhackupc sends emails using Django's template system. Each email consists of two template files:
- `*_subject.txt` — the subject line (one line of text, no HTML)
- `*_message.html` — the email body (HTML)

---

## All Emails the System Sends

| Email | Sent when | App | Template path |
|---|---|---|---|
| Hacker invitation | Organizer sends batch invites | `applications` | `applications/templates/mails/invitation_hacker_*` |
| Mentor invitation | (currently disabled) | `applications` | `applications/templates/mails/invitation_mentor_*` |
| Volunteer invitation | (currently disabled) | `applications` | `applications/templates/mails/invitation_volunteer_*` |
| Confirmation (ticket) | Hacker confirms attendance | `applications` | `applications/templates/mails/confirmation_*` |
| Last reminder | Reminder before confirmation deadline | `applications` | `applications/templates/mails/last_reminder_*` |
| Reimbursement approved | Organizer approves reimbursement | `reimbursement` | `reimbursement/templates/mails/reimbursement_*` |
| Receipt rejected | Organizer rejects uploaded receipt | `reimbursement` | `reimbursement/templates/mails/reject_receipt_*` |
| No reimbursement | Hacker not eligible for reimbursement | `reimbursement` | `reimbursement/templates/mails/no_reimbursement_*` |
| Travel tickets upload | Ask hacker to upload travel receipts | `reimbursement` | `reimbursement/templates/mails/travel_tickets_upload_*` |
| Ticket accepted | Receipt accepted | `reimbursement` | `reimbursement/templates/mails/ticket_accepted_*` |
| Devpost upload | Ask hacker to upload Devpost link | `reimbursement` | `reimbursement/templates/mails/devpost_upload_*` |
| Project invalidated | Devpost project rejected | `reimbursement` | `reimbursement/templates/mails/project_invalidated_*` |
| Devpost approved | Devpost project approved | `reimbursement` | `reimbursement/templates/mails/devpost_approved_*` |
| Email verification | User registers | `user` | `user/templates/mails/verify_email_*` |
| Password reset | User requests password reset | `user` | `user/templates/mails/password_reset_*` |
| Sponsor link | Sponsor account linked | `user` | `user/templates/mails/sponsor_link_*` |

Shared email components (footer, buttons, images) are in `app/templates/mails/include/`.

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
| Application emails (invite, confirmation, reminder) | `applications/emails.py` | `name`, `reimb`, `confirm_url`, `cancel_url`, `hybrid_option`, `token`, `qr_url` |
| Reimbursement emails | `reimbursement/emails.py` | `app`, `reimb`, `confirm_url`, `form_url`, `cancel_url` |
| User emails | `user/emails.py` | varies per email — read the function |

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
````

---

## Phase 2: CSS Reorganization

---

### Task 5: Split `custom-bootstrap.css` into component files

**Files:**
- Modify: `app/templates/base.html` (replace single `<link>` with multiple)
- Create: `app/static/css/bootstrap-overrides/variables.css`
- Create: `app/static/css/bootstrap-overrides/print.css`
- Create: `app/static/css/bootstrap-overrides/glyphicons.css`
- Create: `app/static/css/bootstrap-overrides/scaffolding.css`
- Create: `app/static/css/bootstrap-overrides/typography.css`
- Create: `app/static/css/bootstrap-overrides/grid.css`
- Create: `app/static/css/bootstrap-overrides/tables.css`
- Create: `app/static/css/bootstrap-overrides/forms.css`
- Create: `app/static/css/bootstrap-overrides/buttons.css`
- Create: `app/static/css/bootstrap-overrides/nav.css`
- Create: `app/static/css/bootstrap-overrides/dropdowns.css`
- Create: `app/static/css/bootstrap-overrides/alerts.css`
- Create: `app/static/css/bootstrap-overrides/modals.css`
- Create: `app/static/css/bootstrap-overrides/misc.css`

- [ ] **Step 1: Un-minify `custom-bootstrap.css`**

The file is currently minified (all on a few lines). Before splitting, format it so each rule is on its own line:

```bash
# Install prettier if not available
npm install -g prettier
# Format the file in-place
prettier --write app/static/css/custom-bootstrap.css --parser css
```

If npm is not available, paste the file contents into https://www.cleancss.com/css-beautify/ and replace the file. The un-minified version will be easier to split and maintain going forward.

- [ ] **Step 2: Create `app/static/css/bootstrap-overrides/` directory**

```bash
mkdir -p app/static/css/bootstrap-overrides
```

- [ ] **Step 3: Split the file into component files**

Open `app/static/css/custom-bootstrap.css`. Working from top to bottom, cut each Bootstrap component section into its own file. Use the following CSS class names to identify section boundaries:

| File | Starts at / contains |
|---|---|
| `variables.css` | `html {`, `body {`, base resets at the top of the file |
| `print.css` | `@media print {` |
| `glyphicons.css` | `.glyphicon` |
| `scaffolding.css` | `.container`, `.container-fluid`, row/col classes |
| `typography.css` | `h1,h2,h3`, `.lead`, `.small`, `blockquote`, `code`, `pre` |
| `grid.css` | `.col-xs-`, `.col-sm-`, `.col-md-`, `.col-lg-` |
| `tables.css` | `.table` |
| `forms.css` | `.form-group`, `.form-control`, `.input-group`, `.checkbox`, `.radio` |
| `buttons.css` | `.btn`, `.btn-default`, `.btn-primary` etc. |
| `nav.css` | `.nav`, `.navbar`, `.breadcrumb`, `.pagination`, `.pager`, `.tabs` |
| `dropdowns.css` | `.dropdown`, `.caret`, `.open` |
| `alerts.css` | `.alert`, `.label`, `.badge` |
| `modals.css` | `.modal`, `.fade`, `.in`, `.backdrop` |
| `misc.css` | Everything else (panels, wells, thumbnails, progress bars, list-groups, jumbotron, close, etc.) |

Each file should start with a comment:
```css
/* Bootstrap 3 overrides — <component name> */
```

- [ ] **Step 4: Update `base.html` to load the component files**

In `app/templates/base.html`, find line 53:
```html
<link rel="stylesheet" href="{% static 'css/custom-bootstrap.css' %}">
```

Replace it with one `<link>` per component file, **in the same order** as the sections appeared in the original file:

```html
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/variables.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/print.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/glyphicons.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/scaffolding.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/typography.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/grid.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/tables.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/forms.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/buttons.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/nav.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/dropdowns.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/alerts.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/modals.css' %}">
<link rel="stylesheet" href="{% static 'css/bootstrap-overrides/misc.css' %}">
```

- [ ] **Step 5: Collect static files and visual check**

```bash
python manage.py collectstatic --noinput
python manage.py runserver
```

Open the app in a browser. The page should look exactly the same as before. Check:
- Navbar renders correctly
- Buttons have correct colours and style
- Forms look correct
- Any modal dialogs (try opening one) render correctly

If anything looks broken, the cascade order is off — check that the component files are loaded in the same order the sections appeared in the original file.

---

### Task 6: Audit `main.css` and extract app-specific styles

**Files:**
- Modify: `app/static/css/main.css` (remove app-specific styles)
- Modify (create if needed): `organizers/static/css/organizers.css`
- Modify (create if needed): `reimbursement/static/css/reimbursement.css`

- [ ] **Step 1: Audit `main.css`**

Read through `app/static/css/main.css` (506 lines). For each CSS rule, ask: "Is this only used in one app's templates?" If yes, it belongs in that app's CSS file. If it's used globally (body, navbar, base layout, typography), it stays.

Keep in `main.css`:
- Body background, font, base layout
- Navbar styles
- Footer styles
- Global utility classes used across multiple apps

Move to app-specific files:
- Any class that only appears in templates of a single app (search with `grep -r "class-name" <app>/templates/`)

- [ ] **Step 2: Create app CSS files if needed and move the styles**

If you find styles that belong only to `organizers`, create `organizers/static/css/organizers.css` and move them there. Same for `reimbursement`.

- [ ] **Step 3: Add the CSS link to the app's base template if needed**

For any app that gets a new CSS file, find its base template (e.g. `organizers/templates/organizers_base.html` or whichever template that app's views extend). Add a `{% block extra_head %}` block:

```html
{% block extra_head %}
<link rel="stylesheet" href="{% static 'css/organizers.css' %}">
{% endblock %}
```

**Important:** Templates that extend `base_tabs.html` use `{% block extra_head %}`. Templates that extend `base.html` directly use `{% block head %}`. Check which one the template extends before adding the block.

- [ ] **Step 4: Verify**

```bash
python manage.py runserver
```

Visual check: navigate to affected pages and confirm styles are unchanged.

---

## Phase 3: Views Splitting

**Pattern for every app:** Convert `views.py` → `views/` package with sub-files and an `__init__.py` that re-exports everything. No `urls.py` changes needed.

---

### Task 7: Split `organizers/views.py`

**Files:**
- Delete: `organizers/views.py`
- Create: `organizers/views/__init__.py`
- Create: `organizers/views/lists.py`
- Create: `organizers/views/review.py`
- Create: `organizers/views/batch_ops.py`

**Class/function → file mapping:**

`lists.py`:
- `hacker_tabs`, `volunteer_tabs`, `mentor_tabs`, `sponsor_tabs` (tab helper functions used throughout the file)
- `ApplicationsListView`
- `InviteListView`
- `WaitlistedApplicationsListView`
- `DubiousApplicationsListView`
- `BlacklistApplicationsListView`
- `_OtherApplicationsListView`
- `VolunteerApplicationsListView`
- `SponsorApplicationsListView`
- `SponsorUserListView`
- `MentorApplicationsListView`

`review.py`:
- `add_vote`, `add_comment` (helper functions)
- `ApplicationDetailView`
- `ReviewApplicationView`
- `ReviewApplicationDetailView`
- `ReviewVolunteerApplicationView`
- `ReviewSponsorApplicationView`
- `ReviewMentorApplicationView`
- `ReviewResume`
- `VisualizeResume`

`batch_ops.py`:
- `InviteTeamListView` (contains the core batch invite algorithm)

- [ ] **Step 1: Create `organizers/views/` directory**

```bash
mkdir organizers/views
```

- [ ] **Step 2: Create `organizers/views/lists.py`**

Copy the imports from the top of `organizers/views.py` — all of them, because you will prune unused ones later. Then cut-paste the tab helper functions and all list view classes listed above.

At the top of `lists.py`, add any imports needed by these classes. (Start with all imports from the original file — remove what is not used once the split is complete.)

- [ ] **Step 3: Create `organizers/views/review.py`**

Same process: copy all imports, cut-paste `add_vote`, `add_comment`, and all review view classes listed above.

Note: `ReviewApplicationView` and `ReviewApplicationDetailView` both inherit from `ApplicationDetailView`, which is also in this file — no cross-file import needed.

- [ ] **Step 4: Create `organizers/views/batch_ops.py`**

Copy all imports, cut-paste `InviteTeamListView`.

- [ ] **Step 5: Create `organizers/views/__init__.py`**

This file re-exports every name that any file in the project imports from `organizers.views`. The following names are confirmed callers (grep verified):

```python
from organizers.views.lists import (
    hacker_tabs,
    volunteer_tabs,
    mentor_tabs,
    sponsor_tabs,
    ApplicationsListView,
    InviteListView,
    WaitlistedApplicationsListView,
    DubiousApplicationsListView,
    BlacklistApplicationsListView,
    _OtherApplicationsListView,
    VolunteerApplicationsListView,
    SponsorApplicationsListView,
    SponsorUserListView,
    MentorApplicationsListView,
)
from organizers.views.review import (
    add_vote,
    add_comment,
    ApplicationDetailView,
    ReviewApplicationView,
    ReviewApplicationDetailView,
    ReviewVolunteerApplicationView,
    ReviewSponsorApplicationView,
    ReviewMentorApplicationView,
    ReviewResume,
    VisualizeResume,
)
from organizers.views.batch_ops import (
    InviteTeamListView,
)

__all__ = [
    'hacker_tabs', 'volunteer_tabs', 'mentor_tabs', 'sponsor_tabs',
    'ApplicationsListView', 'InviteListView', 'WaitlistedApplicationsListView',
    'DubiousApplicationsListView', 'BlacklistApplicationsListView',
    '_OtherApplicationsListView', 'VolunteerApplicationsListView',
    'SponsorApplicationsListView', 'SponsorUserListView', 'MentorApplicationsListView',
    'add_vote', 'add_comment',
    'ApplicationDetailView', 'ReviewApplicationView', 'ReviewApplicationDetailView',
    'ReviewVolunteerApplicationView', 'ReviewSponsorApplicationView',
    'ReviewMentorApplicationView', 'ReviewResume', 'VisualizeResume',
    'InviteTeamListView',
]
```

- [ ] **Step 6: Delete the original `organizers/views.py`**

```bash
rm organizers/views.py
```

- [ ] **Step 7: Verify all callers are satisfied**

```bash
grep -r "from organizers.views" . --include="*.py"
grep -r "from organizers import views" . --include="*.py"
```

Confirm every import resolves to a name that `__init__.py` exports.

- [ ] **Step 8: Start the dev server**

```bash
python manage.py runserver
```

Expected: starts with no import errors. Navigate to `/applications/` (organizer view) and confirm it loads.

---

### Task 8: Split `reimbursement/views.py`

**Files:**
- Delete: `reimbursement/views.py`
- Create: `reimbursement/views/__init__.py`
- Create: `reimbursement/views/hacker.py`
- Create: `reimbursement/views/organizer.py`

**Class → file mapping:**

`hacker.py`:
- `ReimbursementHacker`

`organizer.py`:
- `ReimbursementDetail`
- `ReceiptReview` (inherits from `ReimbursementDetail` — both must be in the same file)
- `ReimbursementListView`
- `SendReimbursementListView`

- [ ] **Step 1: Create `reimbursement/views/` directory and sub-files**

Follow the same pattern as Task 7: create the directory, create `hacker.py` and `organizer.py` with the relevant classes, create `__init__.py` with re-exports, delete the original `views.py`.

- [ ] **Step 2: Create `reimbursement/views/__init__.py`**

```python
from reimbursement.views.hacker import ReimbursementHacker
from reimbursement.views.organizer import (
    ReimbursementDetail,
    ReceiptReview,
    ReimbursementListView,
    SendReimbursementListView,
)

__all__ = [
    'ReimbursementHacker',
    'ReimbursementDetail', 'ReceiptReview',
    'ReimbursementListView', 'SendReimbursementListView',
]
```

- [ ] **Step 3: Verify callers and start dev server**

```bash
grep -r "from reimbursement.views" . --include="*.py"
grep -r "from reimbursement import views" . --include="*.py"
python manage.py runserver
```

---

### Task 9: Split `applications/views.py`

**Files:**
- Delete: `applications/views.py`
- Create: `applications/views/__init__.py`
- Create: `applications/views/hacker.py`
- Create: `applications/views/sponsor.py`
- Create: `applications/views/mentor.py`
- Create: `applications/views/draft.py`

**Class/function → file mapping:**

`hacker.py`:
- `VIEW_APPLICATION_TYPE` (constant — also imported by management command)
- `VIEW_APPLICATION_FORM_TYPE` (constant)
- `check_application_exists` (helper)
- `get_deadline` (helper)
- `user_is_in_blacklist` (helper)
- `ConfirmApplication`
- `CancelApplication`
- `HackerDashboard`
- `HackerApplication`

`sponsor.py`:
- `SponsorApplicationView`
- `SponsorDashboard`

`mentor.py`:
- `ConvertHackerToMentor`

`draft.py`:
- `save_draft`

- [ ] **Step 1: Create `applications/views/` directory and sub-files**

Follow the same pattern. `hacker.py` will contain most of the code.

- [ ] **Step 2: Create `applications/views/__init__.py`**

```python
from applications.views.hacker import (
    VIEW_APPLICATION_TYPE,
    VIEW_APPLICATION_FORM_TYPE,
    check_application_exists,
    get_deadline,
    user_is_in_blacklist,
    ConfirmApplication,
    CancelApplication,
    HackerDashboard,
    HackerApplication,
)
from applications.views.sponsor import SponsorApplicationView, SponsorDashboard
from applications.views.mentor import ConvertHackerToMentor
from applications.views.draft import save_draft

__all__ = [
    'VIEW_APPLICATION_TYPE', 'VIEW_APPLICATION_FORM_TYPE',
    'check_application_exists', 'get_deadline', 'user_is_in_blacklist',
    'ConfirmApplication', 'CancelApplication', 'HackerDashboard', 'HackerApplication',
    'SponsorApplicationView', 'SponsorDashboard',
    'ConvertHackerToMentor',
    'save_draft',
]
```

- [ ] **Step 3: Verify callers including the management command**

```bash
grep -r "from applications.views" . --include="*.py"
grep -r "from applications import views" . --include="*.py"
python manage.py runserver
```

- [ ] **Step 4: Verify the management command imports cleanly**

```bash
python manage.py expire_applications --help
```

Expected: prints the help text. If you get an ImportError, `VIEW_APPLICATION_TYPE` is not being re-exported correctly from `__init__.py`.

---

### Task 10: Split `user/views.py`

**Files:**
- Delete: `user/views.py`
- Create: `user/views/__init__.py`
- Create: `user/views/authentication.py`
- Create: `user/views/profile.py`

**Important:** `user/auth.py` already exists as a CAS authentication backend. Do NOT name the views file `auth.py` — use `authentication.py`.

**Class/function → file mapping:**

`authentication.py`:
- `login`, `signup`, `Logout`, `activate`
- `password_reset`, `password_reset_confirm`, `password_reset_complete`, `password_reset_done`
- `verify_email_required`, `set_password`, `send_email_verification`
- `callback`
- `SponsorRegister`

`profile.py`:
- `UserProfile`
- `DeleteAccount`

- [ ] **Step 1: Create `user/views/` directory and sub-files**

Follow the same pattern.

- [ ] **Step 2: Create `user/views/__init__.py`**

```python
from user.views.authentication import (
    login, signup, Logout, activate,
    password_reset, password_reset_confirm, password_reset_complete, password_reset_done,
    verify_email_required, set_password, send_email_verification,
    callback, SponsorRegister,
)
from user.views.profile import UserProfile, DeleteAccount

__all__ = [
    'login', 'signup', 'Logout', 'activate',
    'password_reset', 'password_reset_confirm', 'password_reset_complete', 'password_reset_done',
    'verify_email_required', 'set_password', 'send_email_verification',
    'callback', 'SponsorRegister',
    'UserProfile', 'DeleteAccount',
]
```

- [ ] **Step 3: Verify callers and start dev server**

```bash
grep -r "from user.views" . --include="*.py"
grep -r "from user import views" . --include="*.py"
python manage.py runserver
```

---

### Task 11: Split `baggage/views.py`

**Files:**
- Delete: `baggage/views.py`
- Create: `baggage/views/__init__.py`
- Create: `baggage/views/volunteer.py`
- Create: `baggage/views/hacker.py`

**Class/function → file mapping:**

`volunteer.py`:
- `baggage_checkIn`, `baggage_checkOut` (admin operations)
- `organizer_tabs`
- `BaggageList`, `BaggageHacker`, `BaggageUsers`
- `BaggageAdd`, `BaggageDetail`, `BaggageMap`, `BaggageHistory`
- `BaggageAPI`

`hacker.py`:
- `hacker_tabs`
- `BaggageCurrentHacker`

- [ ] **Step 1: Create sub-files and `__init__.py`, delete original**

Follow the same pattern as Task 7.

- [ ] **Step 2: Create `baggage/views/__init__.py`**

```python
from baggage.views.volunteer import (
    baggage_checkIn,
    baggage_checkOut,
    organizer_tabs,
    BaggageList,
    BaggageHacker,
    BaggageUsers,
    BaggageAdd,
    BaggageDetail,
    BaggageMap,
    BaggageHistory,
    BaggageAPI,
)
from baggage.views.hacker import hacker_tabs, BaggageCurrentHacker

__all__ = [
    'baggage_checkIn', 'baggage_checkOut', 'organizer_tabs',
    'BaggageList', 'BaggageHacker', 'BaggageUsers',
    'BaggageAdd', 'BaggageDetail', 'BaggageMap', 'BaggageHistory',
    'BaggageAPI',
    'hacker_tabs', 'BaggageCurrentHacker',
]
```

- [ ] **Step 3: Verify callers and start dev server**

```bash
grep -r "from baggage.views" . --include="*.py"
grep -r "from baggage import views" . --include="*.py"
python manage.py runserver
```

---

### Task 12: Split `hardware/views.py`

**Files:**
- Delete: `hardware/views.py`
- Create: `hardware/views/__init__.py`
- Create: `hardware/views/hacker.py`
- Create: `hardware/views/admin.py`

**Class/function → file mapping:**

`hacker.py`:
- `HardwareBorrowingsView`
- `HardwareListView`

`admin.py`:
- `hardware_tabs`
- `HardwareAdminRequestsView`
- `HardwareAdminView`

- [ ] **Step 1: Create sub-files and `__init__.py`, delete original**

Follow the same pattern as Task 7.

- [ ] **Step 2: Create `hardware/views/__init__.py`**

```python
from hardware.views.hacker import HardwareBorrowingsView, HardwareListView
from hardware.views.admin import hardware_tabs, HardwareAdminRequestsView, HardwareAdminView

__all__ = [
    'HardwareBorrowingsView', 'HardwareListView',
    'hardware_tabs', 'HardwareAdminRequestsView', 'HardwareAdminView',
]
```

- [ ] **Step 3: Verify callers and start dev server**

```bash
grep -r "from hardware.views" . --include="*.py"
grep -r "from hardware import views" . --include="*.py"
python manage.py runserver
```

- [ ] **Step 3: Final end-to-end check**

With all views split, do a final check:

```bash
python manage.py runserver
```

Navigate through the main flows in the browser:
- Hacker dashboard (`/`)
- Organizer application list (`/applications/`)
- Reimbursement dashboard (`/reimbursement/`)
- Check-in interface (`/checkin/`)
- Stats dashboard (`/stats/`)

All should load without errors.
