# Codebase Refactor Design — myhackupc
**Date:** 2026-04-02
**Author:** Gerard Madrid
**Status:** Approved

---

## Goal

Make the myhackupc codebase maintainable for a volunteer dev team where members are new each year and unfamiliar with the project. The refactor moves things around and splits files — it does **not** improve or rewrite any logic.

---

## Scope

**Included apps:** `applications`, `organizers`, `reimbursement`, `user`, `checkin`, `baggage`, `hardware`, `meals`, `teams`, `stats`, `app` (core)

**Excluded apps (stable, left untouched):** `judging`, `offer`, `discord`

---

## Part 1: Views Splitting

### Principle
Any `views.py` with multiple unrelated concerns becomes a `views/` package. The `views/__init__.py` re-exports **every name** that any other module in the project imports from that views module — not just names referenced in `urls.py`. This is the primary safety guarantee.

Note: Django's URL files typically do `from app import views` and then call `views.SomeClass.as_view()`. As long as `__init__.py` exposes `SomeClass`, Django's URL machinery is unaffected regardless of which sub-file defines it.

### `organizers/views.py` (1,136 lines) → `organizers/views/` package

**Split by class/function (explicit assignments):**

| Name | Target file | Notes |
|---|---|---|
| All `*ListView` classes (hacker, volunteer, mentor, sponsor, dubious, blacklist, waitlist) | `lists.py` | |
| `_OtherApplicationsListView` | `lists.py` | Private base class for volunteer/sponsor/mentor lists; must be in same file as its subclasses |
| `ApplicationDetailView` | `review.py` | Base class — must be in same file as `ReviewApplicationView` which inherits from it |
| `ReviewApplicationView` | `review.py` | |
| Vote and comment helper functions | `review.py` | |
| `InviteTeamListView` | `batch_ops.py` | It is a list view by name but contains the core batch invite algorithm — belongs here |
| Batch email sending orchestration | `batch_ops.py` | Note: the actual `send_batch_emails` function lives in `applications/emails.py`; organizers only has the orchestration |

**`__init__.py` must re-export these specific names** (cross-app imports confirmed in codebase):
- All public view classes (for `urls.py`)
- `_OtherApplicationsListView` — imported by `applications/views.py`
- `hacker_tabs`, `volunteer_tabs`, `mentor_tabs`, `sponsor_tabs` — imported by `checkin/views.py` and `reimbursement/views.py`

### `applications/views.py` (500 lines) → `applications/views/` package

| File | Contents |
|---|---|
| `hacker.py` | Hacker application create/edit/cancel/confirm; shared helpers (`VIEW_APPLICATION_TYPE`, `check_application_exists`, etc.) |
| `mentor.py` | `ConvertHackerToMentor` |
| `sponsor.py` | `SponsorApplicationView`, `SponsorDashboard` |
| `draft.py` | Draft auto-save logic |
| `__init__.py` | Re-exports all view classes and constants |

Note: there are no volunteer-specific view classes in `applications/views.py` — volunteers use the hacker application flow with role detection. No `volunteer.py` is created.

**`__init__.py` must re-export:**
- All public view classes (for `urls.py`)
- `VIEW_APPLICATION_TYPE` — imported by `applications/management/commands/expire_applications.py`
- `VIEW_APPLICATION_FORM_TYPE` — companion constant in the same file; re-export for safety

### Other active apps → `views/` packages

| App | First file | Second file |
|---|---|---|
| `reimbursement` | `hacker.py` — request and receipt upload flow | `organizer.py` — approval and bulk ops. Note: `ReceiptReview` inherits from `ReimbursementDetail`; both must land in the same file (`organizer.py`) |
| `user` | `auth.py` — login, signup, password reset, email verification | `profile.py` — profile editing, account management. Note: `user/auth.py` already exists as a CAS authentication backend — the new views file must be named differently, e.g. `authentication.py` |
| `baggage` | `hacker.py` — hacker-facing baggage flow | `volunteer.py` — volunteer management interface |
| `hardware` | `hacker.py` — hacker request flow | `admin.py` — inventory management |

### Left as single files (small or single concern)
- `checkin/views.py` (263 lines)
- `meals/views.py` (245 lines)
- `teams/views.py` (74 lines)
- `stats/views.py` (381 lines — large but single concern: analytics)

---

## Part 2: CSS Reorganization

### Principle
Styles for a feature live next to that feature's code. If a style only applies to one app, it belongs in that app's `static/css/` folder.

### `custom-bootstrap.css` (1,496 lines) → `bootstrap-overrides/` component files

Split into the following files under `app/static/css/bootstrap-overrides/`, **in this order** to preserve cascade:

| File | Contents |
|---|---|
| `variables.css` | Colors, fonts, spacing resets |
| `print.css` | `@media print` rules |
| `glyphicons.css` | Glyphicon icon font |
| `scaffolding.css` | `.container`, `.container-fluid`, row/col base |
| `typography.css` | Headings, paragraphs, links, blockquote, code |
| `grid.css` | `.col-xs-*`, `.col-sm-*`, `.col-md-*`, `.col-lg-*` |
| `tables.css` | Table overrides |
| `forms.css` | Input, select, textarea overrides |
| `buttons.css` | Button styles and variants |
| `nav.css` | Navbar, tabs, breadcrumbs, pagination |
| `dropdowns.css` | Dropdown menus |
| `alerts.css` | Alert and badge styles |
| `modals.css` | Modal dialogs |
| `misc.css` | Everything else (panels, wells, progress bars, etc.) |

`base.html` gets one `<link>` tag per file, **in the same order as the original file sections**, preserving cascade order.

### `main.css` (506 lines)
Audit for app-specific selectors. Any styles scoped to a specific feature are extracted to that app's `static/css/` file. What remains in `main.css` is global layout, typography baseline, theme colors, navbar, footer only.

### App-specific CSS — existing files (correct, no change needed)
- `baggage/static/css/baggage.css`
- `hardware/static/css/hw.css`
- `applications/static/css/profile.css` — **cross-app note:** this file is also loaded by organizers and reimbursement templates. It is a shared stylesheet, not applications-only. Do not move it into the applications app folder; leave it where it is.
- `checkin/static/css/checkin.css` — already exists and already loaded by checkin templates

### App-specific CSS — may need files created
If `main.css` contains styles for these apps, extract them:
- `reimbursement/static/css/reimbursement.css`
- `organizers/static/css/organizers.css`

### Adding CSS to a template
Templates that extend `base_tabs.html` use `{% block extra_head %}` to add per-page stylesheets.
Templates that extend `base.html` directly use `{% block head %}`.
Do **not** use `{% block extra_css %}` — that block does not exist in this codebase.

---

## Part 3: Documentation

New `docs/` folder at the repo root. The existing README gets a note pointing to both `docs/getting-started.md` and `docs/setting-up.md`.

### `docs/getting-started.md`
- What myhackupc is and who uses it (organizers, hackers, volunteers, mentors)
- Active Django apps: one sentence per app explaining its purpose
- Key config file: `app/hackathon_variables.py` — deadlines, flags, reimbursement limits, touched every year
- Where templates live (per-app `templates/` folders)
- Where styles live (per-app `static/css/` + global `app/static/css/`)
- URL-to-app mapping table

### `docs/setting-up.md`
- Prerequisites, virtualenv, dependencies
- Environment variables and `hackathon_variables.py` setup
- Running the dev server, creating a superuser
- How to verify your changes work
*(Content extracted from README; README updated to point here)*

### `docs/contributing.md`
Worked examples covering the most common yearly changes:
- **Adding/removing a field from the hacker application** — which files to touch: model (`applications/models/hacker.py`), form (`applications/forms/hacker.py`), migration, template
- **Adding/removing a field from volunteer or mentor application** — same pattern, different files
- **Changing the travel reimbursement cap** — just `app/hackathon_variables.py`

### `docs/email-templates.md`
- Table of every email the system sends: email name, which app sends it, template path
- How to edit email content: edit `*_message.html`
- How to edit the subject line: edit `*_subject.txt`
- How to add a new variable to an email: add it to the context dict in the app's `emails.py`, then use `{{ variable_name }}` in the template

---

## Safety Constraints

1. No logic changes — only move code between files, never rewrite it
2. `views/__init__.py` must re-export every name imported from that views module by **any** file in the project — not just `urls.py`. Verify with a project-wide grep after each split.
3. CSS cascade order preserved — `bootstrap-overrides/` files loaded in `base.html` in the same order as sections appeared in the original file
4. No new dependencies introduced
5. All migrations left untouched
6. Excluded apps (`judging`, `offer`, `discord`) are not modified

---

## Execution Order

1. Documentation (`docs/` folder) — zero risk, pure addition
2. CSS reorganization — no logic, visual regression check
3. Views splitting — one app at a time, verify after each:
   - Run the dev server and confirm it starts cleanly
   - For `applications`: also run `python manage.py expire_applications --help` to confirm the management command still imports cleanly (Django dev server does not import management commands on startup, so a broken command will not be caught by a server start check alone)
   - Do a project-wide grep for imports of the converted module to confirm nothing was missed

---

## Out of Scope

- Upgrading Django (currently 3.2 LTS)
- Rewriting any view, model, or form logic
- Adding new features
- Changing URL structure
- Improving test coverage
