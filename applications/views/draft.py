from django.http import JsonResponse

from applications import models, forms
from applications.views.hacker import VIEW_APPLICATION_TYPE, VIEW_APPLICATION_FORM_TYPE
from user.mixins import is_hacker


@is_hacker
def save_draft(request):
    Application = VIEW_APPLICATION_TYPE.get(request.user.type, models.HackerApplication)
    ApplicationForm = VIEW_APPLICATION_FORM_TYPE.get(
        request.user.type, forms.HackerApplicationForm
    )
    d = models.DraftApplication()
    d.user = request.user
    form_keys = set(dict(ApplicationForm().fields).keys())
    valid_keys = set([field.name for field in Application()._meta.get_fields()])
    d.save_dict(
        dict(
            (k, v)
            for k, v in request.POST.items()
            if k in valid_keys.intersection(form_keys) and v
        )
    )
    d.save()
    return JsonResponse({"saved": True})
