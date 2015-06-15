from django.contrib import admin

from .models import School

class SchoolAdmin(admin.ModelAdmin):
    list_display = ('canvas_id', 'name', 'mediasite_root_folder')

admin.site.register(School, SchoolAdmin)