from django.db import models


# Create your models here.

class User(models.Model):
    id = models.TextField()
    name = models.TextField()
    sis_user_id = models.TextField()
    primary_email = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)

class Term(models.Model):
    id = models.TextField()
    name = models.TextField()
    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)

class Enrollment(models.Model):
    type = models.TextField()
    role = models.TextField()
    role_id = models.IntegerField()
    enrollment_state = models.TextField()
    type = models.TextField()
    user = models.ManyToManyField(User)

class Account(models.Model):
    id = models.TextField()
    name = models.TextField()

class ModuleItem(models.Model):
    id = models.TextField()
    module_id = models.TextField()
    title = models.TextField()
    external_url = models.TextField()
    type = models.TextField()
    new_tab = models.BooleanField()

class Module(models.Model):
    id = models.TextField()
    name = models.TextField()
    items = models.ManyToManyField(ModuleItem)
    items_count = models.IntegerField()

class Course(models.Model):
    id = models.TextField()
    sis_course_id = models.TextField(blank=True, null=True)
    name = models.TextField()
    course_code = models.TextField()
    workflow_state = models.TextField()
    account_id = models.TextField()
    enrollment_term_id = models.TextField()
    enrollments = models.ManyToManyField(Enrollment, blank=True, null=True)
    teaching_users = models.ManyToManyField(User, blank=True, null=True)
    term = models.ManyToManyField(Term, blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    total_students = models.IntegerField(null=True)
    modules = models.ManyToManyField(Module, null=True, blank=True)

