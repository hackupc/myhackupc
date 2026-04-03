from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView

from app.utils import reverse
from user import forms
from user.mixins import IsHackerMixin


class UserProfile(IsHackerMixin, TemplateView):
    template_name = 'profile.html'

    def get_context_data(self, *args, **kwargs):
        context = super(UserProfile, self).get_context_data(**kwargs)
        form = forms.ProfileForm(initial={
            'name': self.request.user.name,
            'email': self.request.user.email,
            'type': self.request.user.type if self.request.user.can_change_type() else 'H',
            'non_change_type': self.request.user.get_type_display(),
        }, type_active=self.request.user.can_change_type())
        context.update({'form': form})
        return context

    def post(self, request, *args, **kwargs):
        form = forms.ProfileForm(request.POST, type_active=request.user.can_change_type())
        if form.is_valid():
            name = form.cleaned_data['name']
            request.user.name = name
            if request.user.can_change_type():
                type = form.cleaned_data['type']
                request.user.type = type
            request.user.save()
            messages.success(request, "Profile saved successfully")
            c = self.get_context_data()
        else:
            c = self.get_context_data()
            c.update({'form': form})
        return render(request, self.template_name, c)


class DeleteAccount(IsHackerMixin, TemplateView):
    template_name = 'confirm_delete.html'

    def post(self, request, *args, **kwargs):
        request.user.delete()
        messages.success(request, "User deleted successfully")
        return HttpResponseRedirect(reverse('root'))
