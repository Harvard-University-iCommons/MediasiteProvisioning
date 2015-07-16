from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import School, APIUser, Log

class LogAdmin(admin.ModelAdmin):
    model = Log
    list_display = ('created', 'username', 'error' )

class SchoolAdmin(admin.ModelAdmin):
    list_display = ('canvas_id', 'name', 'mediasite_root_folder')

class APIUserInline(admin.StackedInline):
    model = APIUser

class ExtendedUserAdmin(UserAdmin):
    inlines = (APIUserInline,)

admin.site.register(Log, LogAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.unregister(User)
admin.site.register(User, ExtendedUserAdmin)