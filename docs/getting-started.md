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
- App-specific styles: each app has its own `static/css/` folder (e.g. `baggage/static/css/baggage.css`, `hardware/static/css/hw.css`)

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

Note: `/reimbursement/`, `/baggage/`, and `/hardware/` are only registered when their respective feature flags are enabled in `app/hackathon_variables.py`.

---

## The Most Important Config File

**`app/hackathon_variables.py`** — this is what you touch every year. It contains:
- Application open/close deadlines
- Reimbursement cap amounts
- Feature flags (baggage, hardware, reimbursement, discord)
- Hackathon name, domain, email addresses
- Slack channel IDs

---

## Next Steps

- **Set up your local environment:** see `docs/setting-up.md`
- **Make a change:** see `docs/contributing.md`
- **Edit an email template:** see `docs/email-templates.md`
