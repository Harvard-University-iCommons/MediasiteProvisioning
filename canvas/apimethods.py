import requests
import enum
import json
import sys
from django.conf import settings
from rest_framework.exceptions import APIException
from .serializer import AccountSerializer, CourseSerializer, EnrollmentSerializer, UserSerializer, ModuleSerializer
from .serializer import ModuleItemSerializer, ExternalToolSerializer
from .apimodels import Course, Module, ModuleItem, Account, User, Enrollment, ExternalTool

class CanvasServiceException(Exception):
    _canvas_exception = None

    def __init__(self, canvas_exception,
                 message='Error communicating with Canvas.  Please note this error and contact support.'):
        super(CanvasServiceException, self).__init__(message)
        self._canvas_exception=canvas_exception

class CanvasAppType(enum.Enum):
    File = 'File',
    Page = 'Page',
    Discussion = 'Discussion',
    Assignment = 'Assignment',
    Quiz = 'Quiz',
    SubHeader = 'SubHeader',
    ExternalUrl = 'ExternalUrl'
    ExternalTool = 'ExternalTool'

class CanvasAPI:
    MEDIASITE_EXTERNAL_TOOL_NAME = 'DVS Mediasite Lecture Video'
    MEDIASITE_MODULE_NAME = 'Course Lecture Video'
    MEDIASITE_MODULE_ITEM_NAME = 'Course Lecture Video'
    MEDIASITE_LINK_NAME = 'Lecture Video'

    _user = None

    def __init__(self, user):
        self._user = user

    ##########################################################
    # Accounts
    ##########################################################
    def get_accounts_for_current_user(self):
        response = self.get_canvas_request(partial_url='accounts')
        serializer = AccountSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [Account(**attrs) for attrs in serializer.validated_data]

    ##########################################################
    # Courses
    ##########################################################
    def get_courses_for_account(self, account_id):
        response = self.get_canvas_request(partial_url='accounts/{0}/courses?include=term'.format(account_id))
        serializer = CourseSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [Course(**attrs) for attrs in serializer.validated_data]

    def search_courses(self, account_id, search_term):
        response = self.get_canvas_request(
            partial_url='accounts/{0}/courses?search_term={1}&include=term&published=true&completed=false'
                .format(account_id, search_term))
        serializer = CourseSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            search_results = [Course(**attrs) for attrs in serializer.validated_data]
            for n, course in enumerate(search_results):
                #get the Mediasite external link
                course.canvas_mediasite_external_link = self.get_mediasite_app_external_link(course_id=course.id)

                # set the value of the search results to the modified value
                search_results[n] = course
            return search_results

    def get_course(self, course_id):
        response = self.get_canvas_request(
            partial_url='courses/{0}'.format(course_id)
        )
        serializer = CourseSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            return Course(**serializer.validated_data)

    ##########################################################
    # External tools
    ##########################################################
    def get_mediasite_app_external_link(self, course_id):
        response = self.get_canvas_request(partial_url='courses/{0}/external_tools'.format(course_id))
        serializer = ExternalToolSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            external_tools = [ExternalTool(**attrs) for attrs in serializer.validated_data]
            return next((i for i in external_tools if i.name == CanvasAPI.MEDIASITE_LINK_NAME), None)

    def create_mediasite_app_external_link(self, course_id, consumer_key, shared_secret, url):
        external_link = dict (
            consumer_key=consumer_key,
            shared_secret=shared_secret,
            url=url,
            name=CanvasAPI.MEDIASITE_LINK_NAME,
            privacy_level='public',
            course_navigation=dict (
                enabled=True,
                url=url,
                visibility='members',
                label=CanvasAPI.MEDIASITE_LINK_NAME
            )
        )
        data = {'external_tool': external_link}
        response = self.post_canvas_request(partial_url='courses/{0}/external_tools'.format(course_id), data=data)
        serializer = ExternalToolSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            return ExternalTool(**serializer.validated_data)

    ##########################################################
    # Modules
    ##########################################################
    def get_modules(self, course_id):
        response = self.get_canvas_request(
            partial_url='courses/{0}/modules'.format(course_id)
        )
        serializer = ModuleSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [Module(**attrs) for attrs in serializer.validated_data]

    def create_module(self, course_id, module_name):
        module = Module(name = module_name)
        data = {'module': module.__dict__ }
        response = self.post_canvas_request(partial_url='courses/{0}/modules'.format(course_id), data = data)
        serializer = ModuleSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            return Module(**serializer.validated_data)

    def get_module_by_name(self, course_id, module_name):
        # TODO: what if there are two modules of the same name?
        return next((i for i in self.get_modules(course_id) if i.name == module_name), None)

    def get_or_create_module(self, course_id, module_name):
        module = self.get_module_by_name(course_id, module_name)
        if module is None:
            module = self.create_module(course_id, module_name)
        return module

    ##########################################################
    # Module items
    ##########################################################
    def get_module_items(self, course_id, module_id):
        response = self.get_canvas_request(
            partial_url='courses/{0}/modules/{1}/items'.format(course_id, module_id)
        )
        serializer = ModuleItemSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [ModuleItem(**attrs) for attrs in serializer.validated_data]

    def get_module_item_by_title_and_type(self, course_id, module_id, title, app_type):
        module_items = self.get_module_items(course_id, module_id)
        return next((i for i in module_items if i.title == title and i.type == app_type), None)

    def get_module_item(self, course_id, module_id, module_item_id):
        response = self.get_canvas_request(
            partial_url='courses/{0}/modules/{1}/items/{2}'.format(course_id, module_id, module_item_id)
        )
        serializer = ModuleItemSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            return ModuleItem(**serializer.validated_data)

    def create_module_item(self, course_id, module_item):
        data = { 'module_item' : module_item.__dict__ }
        response = self.post_canvas_request(partial_url='courses/{0}/modules/{1}/items'
                                        .format(course_id, module_item.module_id), data = data)
        serializer = ModuleItemSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            return ModuleItem(**serializer.validated_data)

    def get_mediasite_module_item_by_course(self, course_id):
        mediasite_module = self.get_module_by_name(course_id, module_name=CanvasAPI.MEDIASITE_MODULE_NAME)
        if mediasite_module is not None and mediasite_module.items_count > 0:
            return self.get_module_item_by_title_and_type(course_id, mediasite_module.id,
                                                          title=CanvasAPI.MEDIASITE_MODULE_ITEM_NAME,
                                                          app_type=CanvasAppType.ExternalTool.value)

    def get_or_create_mediasite_module_item(self, course_id, external_url, external_tool_id):
        mediasite_module_item = None
        mediasite_module = self.get_module_by_name(course_id, module_name=CanvasAPI.MEDIASITE_MODULE_NAME)
        if mediasite_module is not None:
            mediasite_module_item = \
                self.get_module_item_by_title_and_type(course_id, mediasite_module.id,
                                                            title=CanvasAPI.MEDIASITE_MODULE_ITEM_NAME,
                                                            app_type=CanvasAppType.ExternalTool.value)
        else:
            mediasite_module = self.create_module(course_id, CanvasAPI.MEDIASITE_MODULE_NAME)

        # we only create the mediasite module item, we don't update it
        # TODO: next phase : look into whether we should update it
        if mediasite_module_item is None:
            mediasite_module_item = ModuleItem(module_id=mediasite_module.id,
                                               title=CanvasAPI.MEDIASITE_MODULE_ITEM_NAME,
                                               type=CanvasAppType.ExternalTool.value,
                                               external_url=external_url,
                                               content_id = external_tool_id)
            mediasite_module_item = self.create_module_item(course_id, mediasite_module_item)

        return mediasite_module_item

    ##########################################################
    # Users, including enrollments
    ##########################################################
    def get_enrollments_for_teachers_and_tas(self, course_id):
        response = self.get_canvas_request(partial_url='courses/{0}/enrollments?type[]={1}&type[]={2}'
                                       .format(course_id, 'TeacherEnrollment', 'TaEnrollment'))
        serializer = EnrollmentSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [Enrollment(**attrs) for attrs in serializer.validated_data]

    def get_enrollments(self, course_id, include_user_email):
        enrollments = self.get_enrollments_for_teachers_and_tas(course_id=course_id)
        # find users for enrollments to add the email address, not available in the
        # enrollments API call, and an expensive call so optional
        if include_user_email:
            for enrollment_counter, enrollment in enumerate(enrollments):
                enrollments[enrollment_counter].user = self.get_user_profile(enrollment.user.id)
        return enrollments

    def get_user_profile(self, user_id):
        response = self.get_canvas_request(partial_url='users/{0}/profile'.format(user_id))
        serializer = UserSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            return User(**serializer.validated_data)

    def get_teaching_users_for_course(self, course_id):
        response = self.get_canvas_request(partial_url='courses/{0}/users?enrollment_type=teacher&include[]=email'
                                            .format(course_id))
        serializer = UserSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [User(**attr) for attr in serializer.validated_data]

    def get_ta_users_for_course(self, course_id):
        response = self.get_canvas_request(partial_url='courses/{0}/users?enrollment_type=ta&include[]=email'
                                       .format(course_id))
        serializer = UserSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [User(**attrs) for attrs in serializer.validated_data]

    ##########################################################
    # Helper methods
    ##########################################################
    @staticmethod
    def get_year_from_term(term):
        year = None
        if term.sis_term_id:
            start_year = int(float(term.sis_term_id[:4]))
            return '{0}-{1}'.format(start_year, start_year + 1)

    @staticmethod
    def get_year_from_start_date(year_start_at):
        # if the course starts in July or later
        if year_start_at.month >= 7:
            return '{0}-{1}'.format(year_start_at.year, year_start_at.year + 1)
        else:
            return '{0}-{1}'.format(year_start_at.year-1, year_start_at.year)
        endif

    ##########################################################
    # API methods
    ##########################################################
    def get_canvas_request(self, partial_url):
        try:
            r = requests.get(url=CanvasAPI.get_canvas_url(partial_url),
                             headers=self.get_canvas_headers())
            r.raise_for_status()
            return r
        except Exception as e:
            raise CanvasServiceException(canvas_exception=e)

    def post_canvas_request(self, partial_url, data):
        try:
            r = requests.post(url=CanvasAPI.get_canvas_url(partial_url),
                              data=json.dumps(data),
                              headers=self.get_canvas_headers())
            r.raise_for_status()
            return r
        except Exception as e:
            raise CanvasServiceException(canvas_exception=e)

    @staticmethod
    def get_canvas_url(partial_url):
        return settings.CANVAS_URL.format(partial_url)

    def get_canvas_headers(self):
        # TODO: now: decrypt encrypted token
        # TODO: what if the user does not have an API key, or an invalid key?
        user_token = self._user.apiuser.canvas_api_key
        return {'Authorization': 'Bearer ' + user_token, 'Content-Type': 'application/json'}
