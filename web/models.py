from django.db import models
from django.contrib.auth.models import User

class School(models.Model):
    canvas_id = models.TextField()
    name = models.TextField()
    mediasite_root_folder = models.TextField(blank=True, null=True)
    consumer_key = models.TextField(blank=True, null=True)
    shared_secret = models.TextField(blank=True, null=True)

class APIUser(models.Model):
    user = models.OneToOneField(User)
    canvas_api_key = models.TextField()
