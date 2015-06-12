from django.db import models

class Account(models.Model):
    id = models.TextField(primary_key=True)
    name = models.TextField()
    mediasite_root_folder = models.TextField(blank=True, null=True)