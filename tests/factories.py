import factory
from django.contrib.auth import get_user_model

from applications.models import APP_CONFIRMED, APP_PENDING
from applications.models.hacker import HackerApplication
from applications.models.mentor import MentorApplication
from applications.models.sponsor import SponsorApplication
from applications.models.volunteer import VolunteerApplication
from user.models import (
    USR_HACKER,
    USR_MENTOR,
    USR_ORGANIZER,
    USR_SPONSOR,
    USR_VOLUNTEER,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"hacker{n}@example.com")
    name = factory.Faker("name")
    type = USR_HACKER
    email_verified = True
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # set_password() is required — views check has_usable_password()
        user = model_class(*args, **kwargs)
        user.set_password("testpass123")
        user.save()
        return user


class OrganizerUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f"organizer{n}@example.com")
    type = USR_ORGANIZER


class DirectorUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f"director{n}@example.com")
    type = USR_ORGANIZER
    is_director = True


class VolunteerUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f"volunteer{n}@example.com")
    type = USR_VOLUNTEER


class MentorUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f"mentor{n}@example.com")
    type = USR_MENTOR


class SponsorUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f"sponsor{n}@example.com")
    type = USR_SPONSOR


class HackerApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HackerApplication

    user = factory.SubFactory(UserFactory)
    status = APP_PENDING
    origin = "Barcelona, Spain"
    description = factory.Faker("text", max_nb_chars=200)
    university = factory.Faker("company")
    degree = "Computer Science"
    kind_studies = "BACHELOR"
    graduation_year = 2026
    tshirt_size = "M"
    diet = "None"
    phone_number = "+34600000000"
    gender = "NA"
    under_age = False
    first_timer = True
    lennyface = "( ͡° ͜ʖ ͡°)"
    online = False


class VolunteerApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VolunteerApplication

    user = factory.SubFactory(VolunteerUserFactory)
    status = APP_PENDING
    origin = "Barcelona, Spain"
    gender = "NA"
    tshirt_size = "M"
    diet = "None"
    under_age = False
    first_timer = True
    lennyface = "( ͡° ͜ʖ ͡°)"
    studies_and_course = "Computer Science"
    quality = "Teamwork"
    weakness = "Perfectionism"
    cool_skill = "Python"
    volunteer_motivation = "I want to help hackers."
    attendance = "1"
    languages = "English"
    night_shifts = "No"
    first_time_volunteer = True
    hear_about_us = "Posters"


class MentorApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MentorApplication

    user = factory.SubFactory(MentorUserFactory)
    status = APP_PENDING
    origin = "Barcelona, Spain"
    gender = "NA"
    tshirt_size = "M"
    diet = "None"
    under_age = False
    first_timer = True
    lennyface = "( ͡° ͜ʖ ͡°)"
    english_level = 3
    attendance = "1"
    online = False
    fluent = "Python, JavaScript"
    experience = "5 years of software development"
    why_mentor = "I want to share my knowledge with students."
    participated = "HackUPC 2023"
    study_work = True
    degree = "Computer Science"
    graduation_year = 2026
    first_time_mentor = True


class SponsorApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SponsorApplication

    user = factory.SubFactory(SponsorUserFactory)
    status = APP_CONFIRMED  # sponsors default to CONFIRMED, not PENDING
    name = factory.Sequence(lambda n: f"Sponsor Corp {n}")
    email = factory.Faker("email")
    phone_number = "+34600000000"
    tshirt_size = "M"
    diet = "None"
    position = "Engineer"
    attendance = "1"
