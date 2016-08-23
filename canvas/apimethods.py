import requests
import enum
import json
import sys
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from operator import itemgetter, attrgetter, methodcaller
from rest_framework.exceptions import APIException
from .serializer import AccountSerializer, CourseSerializer, EnrollmentSerializer, UserSerializer, ModuleSerializer
from .serializer import ModuleItemSerializer, ExternalToolSerializer, LinkSerializer
from .apimodels import Course, Module, ModuleItem, Account, User, Enrollment, ExternalTool, SearchResults, Term, Link

logger = logging.getLogger(__name__)


class CanvasServiceException(Exception):
    _canvas_exception = None

    def __init__(self, canvas_exception,
                 message='Error communicating with Canvas.  Please note this error and contact support.'):
        super(CanvasServiceException, self).__init__(message)
        self._canvas_exception=canvas_exception

    def status_code(self):
        if self._canvas_exception:
            if hasattr(self._canvas_exception, 'response'):
                return self._canvas_exception.response.status_code

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
            # return [Account(**attrs) for attrs in serializer.validated_data if attrs.has_key('sis_account_id')]
            return [Account(**attrs) for attrs in serializer.validated_data]

    ##########################################################
    # Courses
    ##########################################################
    def get_courses_for_account(self, account_id):
        response = self.get_canvas_request(partial_url='accounts/{0}/courses?include=term'.format(account_id))
        serializer = CourseSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            return [Course(**attrs) for attrs in serializer.validated_data]

    def search_courses(self, account_id, search_term, page):
        results = SearchResults()
        terms = list()
        years = list()
        response = self.get_canvas_request(
            partial_url='accounts/{0}/courses?include=term&completed=false&search_term={1}&page={2}&per_page=10'
                .format(account_id, search_term, page))

        # get courses
        serializer = CourseSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            results.search_results = [Course(**attrs) for attrs in serializer.validated_data]

            for n, course in enumerate(results.search_results):
                # get the Mediasite external link
                course.canvas_mediasite_external_link = self.get_mediasite_app_external_link(course_id=course.id, course_term=course.term.name)

                if course.year not in years:
                    years.append(course.year)

                # find and add terms
                if next((t for t in terms if t.name == course.term.name), None) is None:
                    terms.append(course.term)

                # set the value of the search results to the modified value
                results.search_results[n] = course

            results.terms = terms
            results.years = years

        # get links, add them if there is a 'next' or 'prev' page (if there is not then there is only one page)
        # removing the current link
        serializer = LinkSerializer(data=list(response.links.values()), many=True)
        if serializer.is_valid(raise_exception=True):
            links = [Link(**attrs) for attrs in serializer.validated_data]
            # dont allow paging to the current page
            for n, link in enumerate(links):
                if link.page() == page:
                    link.url = None
                links[n] = link

            if next((l for l in links if l.rel == 'next' or l.rel == 'prev'), None) is not None:
                results.links = sorted(list(l for l in links if l.rel != 'current'), key=attrgetter('rel'))

        return results

    def get_course(self, course_id):
        response = self.get_canvas_request(
            partial_url='courses/{0}?include=term'.format(course_id)
        )
        serializer = CourseSerializer(data=response.json())
        if serializer.is_valid(raise_exception=True):
            return Course(**serializer.validated_data)

    ##########################################################
    # External tools
    ##########################################################
    def get_mediasite_app_external_link(self, course_id, course_term):
        response = self.get_canvas_request(partial_url='courses/{0}/external_tools'.format(course_id))
        serializer = ExternalToolSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            external_tools = [ExternalTool(**attrs) for attrs in serializer.validated_data]
            return next((i for i in external_tools if i.name == "{0} {1}".format(CanvasAPI.MEDIASITE_EXTERNAL_TOOL_NAME, course_term)), None)

    def get_mediasite_app_external_links(self, course_id):
        response = self.get_canvas_request(partial_url='courses/{0}/external_tools'.format(course_id))
        serializer = ExternalToolSerializer(data=response.json(), many=True)
        if serializer.is_valid(raise_exception=True):
            external_tools = [ExternalTool(**attrs) for attrs in serializer.validated_data]
            return [i for i in external_tools if CanvasAPI.MEDIASITE_EXTERNAL_TOOL_NAME in i.name ]

    def create_mediasite_app_external_link(self, course_id, course_term, url, consumer_key, shared_secret):
        mediasite_link_name = CanvasAPI.MEDIASITE_LINK_NAME

        # if there is already a external link then we want to distinguish this link in the navigation bar
        # using the term name
        if len(self.get_mediasite_app_external_links(course_id=course_id)) != 0:
            mediasite_link_name = "{0} {1}".format(CanvasAPI.MEDIASITE_LINK_NAME, course_term)

        external_link = dict (
            consumer_key=consumer_key,
            shared_secret=shared_secret,
            url=url,
            name="{0} {1}".format(CanvasAPI.MEDIASITE_EXTERNAL_TOOL_NAME,course_term),
            privacy_level='public',
            course_navigation=dict (
                enabled=True,
                url=url,
                visibility='members',
                text=mediasite_link_name
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

    # This method is not used at this time, due to a change in scope.
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
    # API methods
    ##########################################################

    # def get_canvas_api_key(self, code):
    #     auth_data = dict (
    #         client_id=settings.CANVAS_CLIENT_ID,
    #         redirect_uri=settings.OAUTH_REDIRECT_URI,
    #         client_secret=settings.CANVAS_CLIENT_SECRET,
    #         code=code
    #     )
    #     partial_url='login/oauth2/token?client_id={0}&redirect_uri={1}&client_secret={2}&code={3}'\
    #         .format(settings.CANVAS_CLIENT_ID,
    #                 settings.OAUTH_REDIRECT_URI,
    #                 settings.CANVAS_CLIENT_SECRET,
    #                 code)
    #     r = self.post_canvas_request(partial_url=partial_url, data=None)
    #     return r.json()['access_token']

    def get_canvas_api_key(self, code):
        auth_data = dict (
            client_id=settings.CANVAS_CLIENT_ID,
            redirect_uri=settings.OAUTH_REDIRECT_URI,
            client_secret=settings.CANVAS_CLIENT_SECRET,
            code=code
        )
        partial_url='login/oauth2/token'
        r = self.post_canvas_request(partial_url=partial_url, data=auth_data, use_api=False)
        return r.json()['access_token']

    def get_canvas_request(self, partial_url):
        try:
            r = requests.get(url=CanvasAPI.get_canvas_api_url(partial_url),
                             headers=self.get_canvas_headers())
            r.raise_for_status()
            return r
        except Exception as e:
            raise CanvasServiceException(canvas_exception=e)

    def post_canvas_request(self, partial_url, data, use_api=True):
        try:
            if use_api:
                url = CanvasAPI.get_canvas_api_url(partial_url)
            else:
                url = CanvasAPI.get_canvas_url(partial_url)

            r = requests.post(url=url,
                              data=json.dumps(data),
                              headers=self.get_canvas_headers())
            r.raise_for_status()
            logger.debug("made a {} call to {} via requests".format(
                r.request.method, r.request.url))
            return r
        except Exception as e:
            logger.info("tried to make a {} call to {} via requests with data {}".format(
                r.request.method, r.request.url, r.request.body))
            raise CanvasServiceException(canvas_exception=e)

    @staticmethod
    def get_canvas_api_url(partial_url):
        return settings.CANVAS_URL.format('api/v1/{0}'.format(partial_url))

    @staticmethod
    def get_canvas_url(partial_url):
        return settings.CANVAS_URL.format(partial_url)

    @staticmethod
    def get_canvas_oauth_redirect_url(client_id):
        canvas_oauth_path = '/login/oauth2/auth?client_id={0}&response_type=code&redirect_uri={1}&state={2}'\
            .format(settings.CANVAS_CLIENT_ID, settings.OAUTH_REDIRECT_URI, client_id )
        return settings.CANVAS_URL.format(canvas_oauth_path)

    def get_canvas_headers(self):
        # TODO: now: decrypt encrypted token
        user_token = ""
        try:
            user_token = self._user.apiuser.canvas_api_key
        except ObjectDoesNotExist:
            # do nothing
            pass
        return {'Authorization': 'Bearer ' + user_token, 'Content-Type': 'application/json'}
