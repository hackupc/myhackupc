from __future__ import unicode_literals
from django.db import models
from multiselectfield import MultiSelectField
from app import utils
from .base import *

GENDERS_ES = [
    (NO_ANSWER, "Prefiero no responder"),
    (MALE, "Hombre"),
    (FEMALE, "Mujer"),
    (NON_BINARY, "No binario"),
    (GENDER_OTHER, "Prefiero describirme"),
]

LENGUAGUES_ES = [("Spanish", "Español"), ("Catalan", "Catalán"), ("English", "Inglés")]

ATTENDANCE_ES = [(0, "Viernes"), (1, "Sábado"), (2, "Domingo")]

HEARABOUTUS_ES = [
    ("Posters", "Posters"),
    ("Redes Sociales", "Redes Sociales"),
    ("Mesas en el bar de la FIB", "Mesas en el bar de la FIB"),
    ("Mensajes por grupos de Whatsapp", "Mensajes por grupos de Whatsapp"),
    ("Amigos, compañeros u otras personas", "Amigos, compañeros u otras personas"),
    ("Anuncios online", "Anuncios online"),
    ("Otros", "Otros"),
]


DIETS_ES = [
    (D_NONE, "Sin requerimientos"),
    (D_VEGETARIAN, "Vegetariano"),
    (D_VEGAN, "Vegano"),
    (D_GLUTEN_FREE, "Sin gluten"),
    (D_OTHER, "Otros"),
]

NIGHT_SHIFT_ES = [("No", "No"), ("Yes", "Sí"), ("Maybe", "Puede ser")]


class VolunteerApplication(BaseApplication):

    # gender
    gender = models.CharField(max_length=23, choices=GENDERS_ES, default=NO_ANSWER)

    # diet
    diet = models.CharField(max_length=300, choices=DIETS_ES, default=D_NONE)
    # Where is this person coming from?
    origin = models.CharField(max_length=300)

    # Is this your first hackathon?
    first_timer = models.BooleanField(default=False)

    # Random lenny face
    lennyface = models.CharField(max_length=20, default="-.-")

    # About us
    hear_about_us = models.CharField(max_length=300, choices=HEARABOUTUS_ES, default="")
    other_hear_about_us = models.CharField(max_length=500, blank=True, null=True)

    # University
    graduation_year = models.IntegerField(choices=YEARS, default=DEFAULT_YEAR)
    university = models.CharField(max_length=300)
    degree = models.CharField(max_length=300)

    attendance = MultiSelectField(choices=ATTENDANCE_ES)

    languages = MultiSelectField(choices=LENGUAGUES_ES)
    which_hack = MultiSelectField(choices=PREVIOUS_HACKS_VOLUNTEER)

    cool_skill = models.CharField(max_length=100, null=False)
    first_time_volunteer = models.BooleanField()
    quality = models.CharField(max_length=150, null=False)
    weakness = models.CharField(max_length=150, null=False)

    friends = models.CharField(max_length=100, null=True, blank=True)
    night_shifts = MultiSelectField(choices=NIGHT_SHIFT_ES, default="No")
    studies_and_course = models.CharField(max_length=500, blank=True, default="")
    volunteer_motivation = models.CharField(max_length=500)
    valid = models.BooleanField(default=True)

    def can_be_edit(self, app_type="V"):
        return self.status in [APP_PENDING, APP_DUBIOUS] and not utils.is_app_closed(
            app_type
        )
