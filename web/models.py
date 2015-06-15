from django.db import models

class School(models.Model):
    canvas_id = models.TextField()
    name = models.TextField()
    mediasite_root_folder = models.TextField(blank=True, null=True)
