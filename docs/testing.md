# Testing

This project uses [pytest](https://pytest.org) with [pytest-django](https://pytest-django.readthedocs.io) and [factory-boy](https://factoryboy.readthedocs.io) for automated testing. Tests live in `tests/` and cover the four main application flows: hacker, volunteer, mentor, and sponsor.

---

## Running the tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov

# Run a single file
pytest tests/flows/test_hacker.py

# Run a single test
pytest tests/flows/test_hacker.py::test_hacker_can_submit_application -v
```

Coverage is configured in `setup.cfg`. The report will fail if coverage across `applications`, `organizers`, and `user` drops below 60%.

---

## Structure

```
tests/
├── conftest.py          # Shared fixtures (users, authenticated clients)
├── factories.py         # factory-boy factories for creating test data
└── flows/
    ├── test_hacker.py   # 8 tests covering the hacker application flow
    ├── test_volunteer.py # 5 tests covering the volunteer application flow
    ├── test_mentor.py   # 5 tests covering the mentor application flow
    └── test_sponsor.py  # 3 tests covering the sponsor application flow
```

---

## How it works

### Fixtures (`conftest.py`)

`conftest.py` defines shared pytest fixtures available to every test file.

`**use_locmem_email_backend` (autouse)** — runs automatically for every test. It overrides two Django settings that would otherwise break tests:

- `EMAIL_BACKEND`: swaps SendGrid for Django's in-memory backend so views that send confirmation emails don't fail.
- `STATICFILES_STORAGE`: swaps whitenoise's manifest storage (which requires `collectstatic` to have been run) for a simple one that works without it.

**User fixtures** — each creates a database user of the right type:

```python
hacker_user    # type=USR_HACKER
organizer_user # type=USR_ORGANIZER
volunteer_user # type=USR_VOLUNTEER
mentor_user    # type=USR_MENTOR
sponsor_user   # type=USR_SPONSOR
director_user  # type=USR_ORGANIZER + is_director=True
```

**Client fixtures** — each returns `(client, user)` where the client is already logged in as that user:

```python
hacker_client, organizer_client, volunteer_client,
mentor_client, sponsor_client, director_client
```

Use the tuple unpacking pattern in tests:

```python
def test_something(hacker_client):
    client, user = hacker_client
    response = client.get(reverse("dashboard"))
```

### Factories (`factories.py`)

Factories create realistic model instances without hitting external services. They use `factory.Sequence` for unique fields and `factory.Faker` for realistic fake data.

**Important:** `UserFactory._create()` calls `user.set_password()` before saving. This is required because view mixins (`IsHackerMixin`, `DashboardMixin`, etc.) call `has_usable_password()` and redirect to the password-change page if it returns `False`. Django's default `create()` does not call `set_password()`, so the override is necessary.


| Factory                       | Model                  | Default status                       |
| ----------------------------- | ---------------------- | ------------------------------------ |
| `UserFactory`                 | `User`                 | —                                    |
| `OrganizerUserFactory`        | `User`                 | type=USR_ORGANIZER                   |
| `DirectorUserFactory`         | `User`                 | type=USR_ORGANIZER, is_director=True |
| `HackerApplicationFactory`    | `HackerApplication`    | APP_PENDING                          |
| `VolunteerApplicationFactory` | `VolunteerApplication` | APP_PENDING                          |
| `MentorApplicationFactory`    | `MentorApplication`    | APP_PENDING                          |
| `SponsorApplicationFactory`   | `SponsorApplication`   | APP_CONFIRMED                        |


Override any field when creating an instance:

```python
app = HackerApplicationFactory(user=user, status=APP_INVITED)
```

### Tests (`flows/`)

Each test file covers one applicant type. Tests use `@pytest.mark.django_db` to get database access per test. The pattern is:

1. Set up data (via fixtures or factories)
2. Make an HTTP request via `client.get()` or `client.post()`
3. Assert the response status code and the resulting database state

---

## Key points to know

### `origin` must match `cities.json`

The `origin` field on application forms is validated against a list of cities. It must be in the format `"City, Province, Country"`:

```python
"origin": "Barcelona, Barcelona, Spain"  # correct
"origin": "Barcelona"                    # fails validation
```

### Cancel requires `APP_INVITED`, not `APP_PENDING`

`BaseApplication.can_be_cancelled()` only returns `True` for `APP_INVITED`, `APP_CONFIRMED`, and `APP_LAST_REMINDER`. Testing cancellation with a PENDING application will fail silently (the view will redirect but the status won't change):

```python
app = HackerApplicationFactory(user=user, status=APP_INVITED)  # correct
app = HackerApplicationFactory(user=user, status=APP_PENDING)   # can't be cancelled
```

### `ConfirmApplication` is GET-only

The confirm view (`/application/<uuid>/confirm/`) uses `client.get()`, not `client.post()`. Confirming a PENDING application raises a `ValidationError` inside the model, which the view catches and converts to a 404.

### Organizer vote uses integer PK, not UUID

`ReviewApplicationView.post()` looks up the application with `HackerApplication.objects.get(pk=request.POST.get("app_id"))`. Pass the integer primary key as a string:

```python
data={"app_id": str(app.pk), ...}   # correct
data={"app_id": str(app.uuid), ...} # wrong — lookup will fail
```

### Mentor and sponsor lists require `is_director=True`

`HaveMentorPermissionMixin` and `HaveSponsorPermissionMixin` require either a specific permission or `is_director=True`. A plain `OrganizerUserFactory` user will get a 302 redirect. Use `director_client`:

```python
def test_organizer_can_view_mentor_list(director_client):  # correct
def test_organizer_can_view_mentor_list(organizer_client): # 302, not 200
```

### Sponsor submission uses a token URL, not the dashboard

Sponsors apply via a unique invite URL (`/sponsor/<uid>/<token>/`), not by logging in. The token comes from the `user.models.Token` model (not Django's password reset). Test it by constructing the URL directly:

```python
token_obj = Token.objects.create(user=sponsor_user)
uid = urlsafe_base64_encode(force_bytes(sponsor_user.pk))
url = f"/sponsor/{uid}/{token_obj.uuid_str()}/"
client.post(url, data=VALID_SPONSOR_FORM)
```

The view renders `sponsor_submitted.html` on success (status 200), not a redirect.

---

## Adding a new test

### Adding a test to an existing file

Open the relevant file in `tests/flows/` and add a function:

```python
@pytest.mark.django_db
def test_hacker_cannot_edit_after_review(hacker_client):
    client, user = hacker_client
    app = HackerApplicationFactory(user=user, status=APP_INVITED)
    response = client.get(reverse("application"))
    # invited hackers should not see the edit form
    assert response.status_code == 302
```

Use `@pytest.mark.django_db` on every test that touches the database. Use the fixtures from `conftest.py` as parameters — pytest injects them automatically.

### Adding a test for a new applicant type

1. Add a `UserFactory` subclass in `tests/factories.py` with the correct `type` value.
2. Add an `ApplicationFactory` subclass with all required fields (run the form in a browser or read the model to find required fields).
3. Add user and client fixtures to `tests/conftest.py` following the existing pattern.
4. Create `tests/flows/test_<type>.py` and write your tests.

### Adding a factory for a new model

```python
class MyModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MyModel

    # Use factory.Sequence for fields that must be unique
    name = factory.Sequence(lambda n: f"Name {n}")

    # Use factory.Faker for realistic fake data
    description = factory.Faker("text", max_nb_chars=200)

    # Use factory.SubFactory to link related models
    user = factory.SubFactory(UserFactory)

    # Hard-code constants where variation isn't needed
    status = APP_PENDING
```

---

## CI

Tests run automatically on CircleCI on every push. The CI config is at `.circleci/config.yml`. It runs:

```bash
pytest --cov   # runs tests and generates coverage
flake8         # lints the codebase
```

Both must pass for a build to go green.