from django.db import models

class Search(models.Model):
    accounts = list()
    search_term = models.TextField()
