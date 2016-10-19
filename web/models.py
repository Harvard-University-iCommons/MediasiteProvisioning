from django.contrib.auth.models import User
from django.db import models


class School(models.Model):
    canvas_id = models.TextField()
    name = models.TextField()
    mediasite_root_folder = models.TextField()
    consumer_key = models.TextField(blank=True, null=True)
    shared_secret = models.TextField(blank=True, null=True)
    catalog_show_date = models.BooleanField(default=False, null=False)
    catalog_show_time = models.BooleanField(default=False, null=False)
    catalog_items_per_page = models.IntegerField(blank=100, null=100)


class APIUser(models.Model):
    user = models.OneToOneField(User)
    canvas_api_key = models.TextField()


class Log(models.Model):
    username = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now=True)
    error = models.TextField()

