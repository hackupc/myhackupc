from django.contrib import admin
from meals import models


class MealsMealAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'times', 'opened', 'starts', 'ends'
    )
    search_fields = (
        'name__unaccent',
    )

    def get_actions(self, request):
        return []


class MealsEatenAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'meal', 'user', 'time'
    )
    search_fields = (
        'meal__name__unaccent', 'user__name__unaccent', 'user__email__unaccent'
    )
    list_filter = (
        'meal', 'user'
    )

    def get_actions(self, request):
        return []


admin.site.register(models.Meal, admin_class=MealsMealAdmin)
admin.site.register(models.Eaten, admin_class=MealsEatenAdmin)
