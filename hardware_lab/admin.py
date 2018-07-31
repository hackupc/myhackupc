from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from hardware_lab import models

class HardwareTypeAdmin(admin.ModelAdmin):
	def image_tag(self, obj):
		return format_html('<img src="{}" />'.format(obj.image.url))

	image_tag.short_description = 'Image'

	list_display = ['name', 'image_tag']

class HardwareItemAdmin(admin.ModelAdmin):
	list_display = ['label', 'hardware_type', 'comments']


admin.site.register(models.HardwareType, HardwareTypeAdmin)
admin.site.register(models.HardwareItem, HardwareItemAdmin)
admin.site.register(models.LogMessage)