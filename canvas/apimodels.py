from django.db import models


# Create your models here.

class BaseSerializedModel(models.Model):
    id = models.IntegerField()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class User(BaseSerializedModel):
    name = models.TextField()
    sis_user_id = models.TextField()
    primary_email = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)

class Term(BaseSerializedModel):
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

class Account(BaseSerializedModel):
    name = models.TextField()

class ModuleItem(BaseSerializedModel):
    module_id = models.TextField()
    title = models.TextField()
    external_url = models.TextField()
    type = models.TextField()
    new_tab = models.BooleanField()

class Module(BaseSerializedModel):
    name = models.TextField()
    items = models.ManyToManyField(ModuleItem)
    items_count = models.IntegerField()

class Course(BaseSerializedModel):
    sis_course_id = models.TextField(blank=True, null=True)
    name = models.TextField()
    course_code = models.TextField()
    workflow_state = models.TextField()
    account_id = models.TextField()
    enrollment_term_id = models.TextField()
    enrollments = models.ManyToManyField(Enrollment, blank=True, null=True)
    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    total_students = models.IntegerField(null=True)
    modules = models.ManyToManyField(Module, null=True, blank=True)
    teaching_users = list()
    term = None
    canvas_mediasite_module_item = None

