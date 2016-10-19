from django.db import models

# Create your models here.

class BaseSerializedModel(models.Model):
    id = models.IntegerField(blank=True, null=True)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class User(BaseSerializedModel):
    name = models.TextField()
    sis_user_id = models.TextField()
    primary_email = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    time_zone = models.TextField(blank=True, null=True)

class Term(BaseSerializedModel):
    name = models.TextField()
    start_at = models.DateTimeField(blank=True, null=True)
    end_at = models.DateTimeField(blank=True, null=True)
    sis_term_id = models.TextField(blank=True, null=True)

class Enrollment(BaseSerializedModel):
    type = models.TextField()
    role = models.TextField()
    enrollment_state = models.TextField()
    role_id = models.IntegerField(blank=True, null=True)
    user = None

    def __init__(self, **kwargs):
        # Enrollment has a hierarchy which needs to be manually initialized
        self.__dict__.update(kwargs)
        user = kwargs['user']
        if user:
            self.user = User(**user)

class Account(BaseSerializedModel):
    name = models.TextField()
    sis_account_id = models.TextField(blank=True, null=True, default="")

class ModuleItem(BaseSerializedModel):
    module_id = models.TextField()
    title = models.TextField()
    external_url = models.TextField()
    html_url = models.TextField()
    type = models.TextField()
    content_id = models.IntegerField()

class Module(BaseSerializedModel):
    name = models.TextField()
    items = models.ManyToManyField(ModuleItem)
    items_count = models.IntegerField()

class Course(BaseSerializedModel):
    sis_course_id = models.TextField(blank=True, null=True, default="")
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
    year = None
    canvas_mediasite_module_item = None
    canvas_mediasite_external_link = None

    def __init__(self, **kwargs):
        # Course has a hierarchy which needs to be manually initialized
        self.__dict__.update(kwargs)
        term = kwargs['term']

        if term:
            self.term = Term(**term)

        # If the term is set to "Default Term" we know that it is bad data, so we get rid of it and rely on
        # other methods to get the term
        if self.term.name == "Default Term":
            self.term = None

        if self.term is not None:
            self.year = Course.get_year_from_term(self.term)
        if self.year is None and self.start_at is not None:
            self.year = Course.get_year_from_start_date(self.start_at)
        # setup the default term
        # TODO: this logic could be improved to look at course dates, but since
        # we should be getting good data from Canvas there should be no need
        if self.term is None:
            self.term = Term(name='Full Year {0}'.format(self.year), start_at=self.start_at)

    ##########################################################
    # Helper methods
    ##########################################################
    @staticmethod
    def get_year_from_term(term):
        year = None

        # If it's an Ongoing term, do not set the year explicitly(TLT-2856)
        if term.name.lower()== 'ongoing':
            return year

        try:
            if hasattr(term, 'sis_term_id'):
                start_year = int(float(term.sis_term_id[:4]))
                return '{0}-{1}'.format(start_year, start_year + 1)
            elif term.name:
                #If the user doesn't see the sis_term_id attribute, use the
                # term name to deduce the year
                start_year = int(float(term.name[:4]))
                return '{0}-{1}'.format(start_year, start_year + 1)
        except:
            return year


    @staticmethod
    def get_year_from_start_date(year_start_at):
        # if the course starts in July or later
        if year_start_at.month >= 7:
            return '{0}-{1}'.format(year_start_at.year, year_start_at.year + 1)
        else:
            return '{0}-{1}'.format(year_start_at.year-1, year_start_at.year)
        endif

class ExternalTool(BaseSerializedModel):
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    domain = models.TextField(blank=True, null=True)
    consumer_key = models.TextField(blank=True, null=True)

class Link(BaseSerializedModel):
    url = models.TextField()
    rel = models.TextField()

    def page(self):
        page = 0
        if self.url:
            page_html = '&page='
            page_index = self.url.find(page_html)
            if page_index != -1:
                page = self.url[page_index + len(page_html):len(self.url) ]
                page_index = page.find('&')
                if page_index != -1:
                    page = page[0:page_index]
        return page

class SearchResults(models.Model):
    search_results = list()
    terms = list()
    years = list()
    links = list()
    count = None
    school = None
