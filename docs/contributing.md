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


| Layer    | Volunteer                                                           | Mentor                          |
| -------- | ------------------------------------------------------------------- | ------------------------------- |
| Model    | `applications/models/volunteer.py`                                  | `applications/models/mentor.py` |
| Form     | `applications/forms/volunteer.py`                                   | `applications/forms/mentor.py`  |
| Template | `applications/templates/` (look for volunteer/mentor form template) | same                            |


Run `python manage.py makemigrations && python manage.py migrate` after changing the model.

---

## Example 3: Changing the Travel Reimbursement Cap

File: `app/hackathon_variables.py`

Find and update the reimbursement limit variables. No migration or code change needed — these are config values read at runtime.

---

## Where to Look for Other Things


| What you want to change                                 | Where to look                         |
| ------------------------------------------------------- | ------------------------------------- |
| Application status flow (pending → invited → confirmed) | `applications/models/base.py`         |
| Who can review applications and vote                    | `organizers/views/review.py`          |
| Batch invite algorithm                                  | `organizers/views/batch_ops.py`       |
| Email content                                           | See `docs/email-templates.md`         |
| Check-in logic                                          | `checkin/views.py`                    |
| User roles and permissions                              | `user/models.py`, `user/mixins.py`    |
| Hackathon name, dates, deadlines                        | `app/hackathon_variables.py`          |
| Global styles                                           | `app/static/css/main.css`             |
| Bootstrap component styles                              | `app/static/css/bootstrap-overrides/` |


