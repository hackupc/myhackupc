from django.contrib import admin

from checkin import models


# Register your models here.

class CheckinAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'type', 'application', 'update_time'
    )
    search_fields = ('user__email__unaccent', 'user__name__unaccent', 'hacker__user__name__unaccent',
                     'hacker__user__email__unaccent', 'volunteer__user__name__unaccent',
                     'volunteer__user__email__unaccent', 'mentor__user__name__unaccent',
                     'mentor__user__email__unaccent', 'sponsor__user__name__unaccent',
                     'sponsor__user__email__unaccent')
    date_hierarchy = 'update_time'
    list_filter = ('user', )
    actions = ['delete_selected', ]


admin.site.register(models.CheckIn, admin_class=CheckinAdmin)
