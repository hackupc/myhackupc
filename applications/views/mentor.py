from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.views.generic import TemplateView

from app.utils import reverse


class ConvertHackerToMentor(TemplateView):
    template_name = "convert_mentor.html"

    def get(self, request, *args, **kwargs):
        if request.user.application.is_invalid():
            return super(ConvertHackerToMentor, self).get(request, *args, **kwargs)
        return Http404

    def post(self, request, *args, **kwargs):
        if request.user.application.is_invalid():
            request.user.set_mentor()
            request.user.save()
            messages.success(request, "Thanks for coming as mentor!")
        else:
            messages.error(request, "You have no permissions to do this")
        return HttpResponseRedirect(reverse("dashboard"))
