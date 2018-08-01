from django.contrib import admin
from django.utils.html import format_html

# Register your models here.
from hardware import models

class TypeAdmin(admin.ModelAdmin):
	def image_tag(self, obj):
		return format_html('<img src="{}" />'.format(obj.image.url))

	image_tag.short_description = 'Image'

	list_display = ['name', 'image_tag']

class ItemAdmin(admin.ModelAdmin):
	list_display = ['label', 'item_type', 'comments']

class RequestAdmin(admin.ModelAdmin):
	def remaining_time(self, obj):
		return obj.get_remaining_time()
	list_display = ['user', 'item_type', 'timestamp', 'remaining_time']


admin.site.register(models.ItemType, TypeAdmin)
admin.site.register(models.Item, ItemAdmin)
admin.site.register(models.Request, RequestAdmin)
admin.site.register(models.LogMessage)