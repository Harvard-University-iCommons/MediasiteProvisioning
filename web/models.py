from django.contrib.auth.models import User
from django.db import models


class School(models.Model):
    canvas_id = models.TextField()
    name = models.TextField()
    mediasite_root_folder = models.TextField(blank=True, null=True)
    consumer_key = models.TextField(blank=True, null=True)
    shared_secret = models.TextField(blank=True, null=True)
    catalog_show_date = models.BooleanField(default=False, null=False)
    catalog_show_time = models.BooleanField(default=False, null=False)
    catalog_items_per_page = models.IntegerField(blank=100, null=100)

    @property
    def can_be_provisioned(self):
        # A school is a valid choice in the form dropdown if it has all the
        # information required to reliably provision a lecture video Canvas
        # integration (consumer key and secret can fall back to values in
        # SETTINGS if needed, but canvas_id and mediasite_root_folder should be
        # specified for each school to be able to query canvas and create the
        # mediasite folder structure).
        return bool(self.canvas_id) and bool(self.mediasite_root_folder)


class APIUser(models.Model):
    user = models.OneToOneField(User)
    canvas_api_key = models.TextField()


class Log(models.Model):
    username = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now=True)
    error = models.TextField()

