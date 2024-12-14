from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import Http404
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views import View
from app.utils import hacker_tabs, reverse
from app.views import TabsView
from applications import models
from checkin.models import CheckIn
from user.mixins import IsOrganizerMixin


class WhoAreU(IsOrganizerMixin, TabsView):
    template_name = 'whoareu.html'
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
        

class WhoAreUAPI(View, IsOrganizerMixin):

    def post(self, request, *args, **kwargs):
        qrid = request.POST.get('qr_id', None)

        if not qrid:
            return JsonResponse({'error': 'Missing QR. Trying to trick us?', 'success': False})

        # check if the QR code is valid
        checkin = CheckIn.objects.filter(qr_identifier=qrid).first()
        if not checkin:
            return JsonResponse({'error': '404-code-not-found', 'success': False})
            
        # get the data of the user who checked in
        # we dont know if its a hacker or a volunteer or a mentor or a sponsor
        hacker_application = models.HackerApplication.objects.filter(checkin=checkin).first()
        if not hacker_application:
            volunteer_application = models.VolunteerApplication.objects.filter(checkin=checkin).first()
            if not volunteer_application:
                mentor_application = models.MentorApplication.objects.filter(checkin=checkin).first()
                if not mentor_application:
                    sponsor_application = models.SponsorApplication.objects.filter(checkin=checkin).first()
                    if not sponsor_application:
                        return JsonResponse({'error': '404-application-not-found', 'success': False})
                    else:
                        type = 'sponsor'    
                        user = sponsor_application.user    
                        appl = sponsor_application
                else:
                    type = 'mentor'
                    user = mentor_application.user
                    appl = mentor_application
            else:
                type = 'volunteer'
                user = volunteer_application.user
                appl = volunteer_application
        else:
            type = 'hacker'
            user = hacker_application.user
            appl = hacker_application
        
        # print(user.__dict__)

        return JsonResponse({'type': type,
                             'name': user.get_full_name(),
                             'diet': appl.diet,
                             'uuid': appl.uuid,
                              'success': True
                             })
        
        
