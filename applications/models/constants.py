from datetime import datetime
from app import utils, hackathon_variables

APP_PENDING = 'P'
APP_REJECTED = 'R'
APP_INVITED = 'I'
APP_LAST_REMIDER = 'LR'
APP_CONFIRMED = 'C'
APP_CANCELLED = 'X'
APP_ATTENDED = 'A'
APP_EXPIRED = 'E'
APP_DUBIOUS = 'D'
APP_INVALID = 'IV'
APP_BLACKLISTED = 'BL'

PENDING_TEXT = 'Under review'
DUBIOUS_TEXT = 'Dubious'
BLACKLIST_TEXT = 'Blacklisted'
STATUS = [
    (APP_PENDING, PENDING_TEXT),
    (APP_REJECTED, 'Wait listed'),
    (APP_INVITED, 'Invited'),
    (APP_LAST_REMIDER, 'Last reminder'),
    (APP_CONFIRMED, 'Confirmed'),
    (APP_CANCELLED, 'Cancelled'),
    (APP_ATTENDED, 'Attended'),
    (APP_EXPIRED, 'Expired'),
    (APP_DUBIOUS, DUBIOUS_TEXT),
    (APP_INVALID, 'Invalid'),
    (APP_BLACKLISTED, BLACKLIST_TEXT)
]

NO_ANSWER = 'NA'
MALE = 'M'
FEMALE = 'F'
NON_BINARY = 'NB'
GENDER_OTHER = 'X'

GENDERS = [
    (NO_ANSWER, 'Prefer not to answer'),
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (NON_BINARY, 'Non-binary'),
    (GENDER_OTHER, 'Prefer to self-describe'),
]

D_SELECT = ''
D_NONE = 'None'
D_VEGETARIAN = 'Vegetarian'
D_VEGAN = 'Vegan'
#D_NO_PORK = 'No pork'
D_GLUTEN_FREE = 'Gluten-free'
D_OTHER = 'Others'

DIETS = [
    (D_SELECT, '- Select a diet -'),
    (D_NONE, 'No requirements'),
    (D_VEGETARIAN, 'Vegetarian'),
    (D_VEGAN, 'Vegan'),
    #(D_NO_PORK, 'No pork'),
    (D_GLUTEN_FREE, 'Gluten-free'),
    (D_OTHER, 'Others')
]

T_SELECT = ''
T_XXS = 'XXS'
T_XS = 'XS'
T_S = 'S'
T_M = 'M'
T_L = 'L'
T_XL = 'XL'
T_XXL = 'XXL'
T_XXXL = 'XXXL'

TSHIRT_SIZES = [
    (T_SELECT, '- Select a t-shirt size -'),
    (T_XS, "Unisex - XS"),
    (T_S, "Unisex - S"),
    (T_M, "Unisex - M"),
    (T_L, "Unisex - L"),
    (T_XL, "Unisex - XL"),
    (T_XXL, "Unisex - XXL"),
    (T_XXXL, "Unisex - XXXL"),
]

DEFAULT_TSHIRT_SIZE = T_SELECT

ATTENDANCE = [
    (0, "Friday"),
    (1, "Saturday"),
    (2, "Sunday")
]

HACK_NAME = getattr(hackathon_variables, 'HACKATHON_NAME', "HackAssistant")
EXTRA_NAME = [' 2016 Fall', ' 2016 Winter', ' 2017 Fall', ' 2017 Winter', ' 2018', ' 2019', ' 2021', ' 2022', ' 2023', ' 2024']
PREVIOUS_HACKS = [(i, HACK_NAME + EXTRA_NAME[i]) for i in range(0, len(EXTRA_NAME))]

YEARS = [(int(size), size) for size in ('2024 2025 2026 2027 2028 2029 2030 2031'.split(' '))]
DEFAULT_YEAR = datetime.now().year + 1

ENGLISH_LEVEL = [(i, str(i)) for i in range(1, 5 + 1)]

DUBIOUS_NONE = 'OK'
DUBIOUS_CV = 'INVALID_CV'
DUBIOUS_GRADUATION_YEAR = 'LATE_GRAD'
DUBIOUS_NOT_STUDENT = 'NOT_STUDENT'
DUBIOUS_SCHOOL = 'INVALID_SCHOOL'
DUBIOUS_OTHER = 'OTHER'

DUBIOUS_TYPES = [
    (DUBIOUS_NONE, 'Not dubious'),
    (DUBIOUS_CV, 'Invalid CV'),
    (DUBIOUS_GRADUATION_YEAR, 'Invalid graduation year'),
    (DUBIOUS_NOT_STUDENT, 'Not a student'),
    (DUBIOUS_SCHOOL, 'Invalid school'),
    (DUBIOUS_OTHER, 'Other')
]
