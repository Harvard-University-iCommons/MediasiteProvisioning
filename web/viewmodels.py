from django.db import models

class SearchResults(models.Model):
    search_results = list()
    terms = list()
    years = list()
    count = None
    school = None
