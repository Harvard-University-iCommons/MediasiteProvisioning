import requests
import enum
import json
from .serializer import AccountSerializer, CourseSerializer, EnrollmentSerializer, UserSerializer, ModuleSerializer
from .serializer import ModuleItemSerializer, ExternalToolSerializer
from .apimodels import Course, Module, ModuleItem, Account, User, Enrollment, ExternalTool

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
    # MEDIASITE_EXTERNAL_TOOL_NAME = 'Mediasite'
    MEDIASITE_EXTERNAL_TOOL_NAME = 'DVS Mediasite Lecture Video'
    MEDIASITE_MODULE_NAME = 'Course Lecture Video'
    MEDIASITE_MODULE_ITEM_NAME = 'Course Lecture Video'
    MEDIASITE_LINK_NAME = 'Lecture Video'

    ##########################################################
    # Accounts
    ##########################################################
    @staticmethod
    def get_accounts_for_current_user():
        json = CanvasAPI.get_canvas_request(partial_url='accounts')
        serializer = AccountSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return [Account(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def get_mediasite_app_external_tool(account_id):
        json = CanvasAPI.get_canvas_request(partial_url='accounts/{0}/external_tools'.format(account_id))
        serializer = ExternalToolSerializer(data=json, many=True)
        if serializer.is_valid():
            external_tools = [ExternalTool(**attrs) for attrs in serializer.validated_data]
            return next((i for i in external_tools
                         if i.name == CanvasAPI.MEDIASITE_EXTERNAL_TOOL_NAME
                         and i.type == CanvasAppType.ExternalTool.value), None)
        else:
            errors = serializer.errors



    ##########################################################
    # Courses
    ##########################################################
    @staticmethod
    def get_courses_for_account(account_id):
        json = CanvasAPI.get_canvas_request(partial_url='accounts/{0}/courses?include=term'.format(account_id))
        serializer = CourseSerializer(data=json, many=True)
        if serializer.is_valid():
            return [Course(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def search_courses(account_id, search_term):
        json = CanvasAPI.get_canvas_request(
            partial_url='accounts/{0}/courses?search_term={1}&include=term&published=true&completed=false'
                .format(account_id, search_term))
        serializer = CourseSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            search_results = [Course(**attrs) for attrs in serializer.validated_data]
            for n, course in enumerate(search_results):
                # update the enrollment data which is not pulled by the search API
                if False:
                    course.enrollments = CanvasAPI.get_enrollments(course_id=course.id, update_user_email=False)

                # get the teaching users
                if False:
                    course.teaching_users = CanvasAPI.get_teaching_users_for_course(course.id)

                # get the Mediasite module
                course.canvas_mediasite_module_item = CanvasAPI.get_mediasite_module_item_by_course(course.id)
                # TODO:validate that the Canvas Mediasite module points to a real catalog?

                # set the value of the search results to the modified value
                search_results[n] = course

            return search_results
        else:
            errors = serializer.errors

    @staticmethod
    def get_course(course_id):
        json = CanvasAPI.get_canvas_request(
            partial_url='courses/{0}'.format(course_id)
        )
        serializer = CourseSerializer(data=json)
        validated = serializer.is_valid()
        if validated:
            return Course(**serializer.validated_data)
        else:
            errors = serializer.errors

    # @staticmethod
    # def get_mediasite_app_external_tool(course_id):
    #     json = CanvasAPI.get_canvas_request(partial_url='courses/{0}/external_tools'.format(course_id))
    #     serializer = ExternalToolSerializer(data=json, many=True)
    #     if serializer.is_valid():
    #         external_tools = [ExternalTool(**attrs) for attrs in serializer.validated_data]
    #         return next((i for i in external_tools if i.name == CanvasAPI.MEDIASITE_EXTERNAL_TOOL_NAME), None)
    #     else:
    #         errors = serializer.errors

    ##########################################################
    # Modules
    ##########################################################
    @staticmethod
    def get_modules(course_id):
        json = CanvasAPI.get_canvas_request(
            partial_url='courses/{0}/modules'.format(course_id)
        )
        serializer = ModuleSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return [Module(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def create_module(course_id, module_name):
        module = Module(name = module_name)
        data = {'module': module.__dict__ }
        json = CanvasAPI.post_canvas_request(partial_url='courses/{0}/modules'.format(course_id), data = data)
        serializer = ModuleSerializer(data=json)
        if serializer.is_valid():
            return Module(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def get_module_by_name(course_id, module_name):
        # TODO: what if there are two modules of the same name?
        return next((i for i in CanvasAPI.get_modules(course_id) if i.name == module_name), None)

    @staticmethod
    def get_or_create_module(course_id, module_name):
        module = CanvasAPI.get_module_by_name(course_id, module_name)
        if module is None:
            module = CanvasAPI.create_module(course_id, module_name)
        return module

    ##########################################################
    # Module items
    ##########################################################
    @staticmethod
    def get_module_items(course_id, module_id):
        json = CanvasAPI.get_canvas_request(
            partial_url='courses/{0}/modules/{1}/items'.format(course_id, module_id)
        )
        serializer = ModuleItemSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return [ModuleItem(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def get_module_item_by_title_and_type(course_id, module_id, title, app_type):
        module_items = CanvasAPI.get_module_items(course_id, module_id)
        return next((i for i in module_items if i.title == title and i.type == app_type), None)

    @staticmethod
    def get_module_item(course_id, module_id, module_item_id):
        json = CanvasAPI.get_canvas_request(
            partial_url='courses/{0}/modules/{1}/items/{2}'.format(course_id, module_id, module_item_id)
        )
        serializer = ModuleItemSerializer(data=json)
        validated = serializer.is_valid()
        if validated:
            return ModuleItem(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def create_module_item(course_id, module_item):
        data = { 'module_item' : module_item.__dict__ }
        json = CanvasAPI.post_canvas_request(partial_url='courses/{0}/modules/{1}/items'
                                             .format(course_id, module_item.module_id), data = data)
        serializer = ModuleItemSerializer(data=json)
        if serializer.is_valid():
            return ModuleItem(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def get_mediasite_module_item_by_course(course_id):
        mediasite_module = CanvasAPI.get_module_by_name(course_id, module_name=CanvasAPI.MEDIASITE_MODULE_NAME)
        if mediasite_module is not None and mediasite_module.items_count > 0:
            return CanvasAPI.get_module_item_by_title_and_type(course_id, mediasite_module.id,
                                                               title=CanvasAPI.MEDIASITE_MODULE_ITEM_NAME,
                                                               app_type=CanvasAppType.ExternalTool.value)

    @staticmethod
    def get_or_create_mediasite_module_item(course_id, external_url, external_tool_id):
        mediasite_module_item = None
        mediasite_module = CanvasAPI.get_module_by_name(course_id, module_name=CanvasAPI.MEDIASITE_MODULE_NAME)
        if mediasite_module is not None:
            mediasite_module_item = \
                CanvasAPI.get_module_item_by_title_and_type(course_id, mediasite_module.id,
                                                            title=CanvasAPI.MEDIASITE_MODULE_ITEM_NAME,
                                                            app_type=CanvasAppType.ExternalTool.value)
        else:
            mediasite_module = CanvasAPI.create_module(course_id, CanvasAPI.MEDIASITE_MODULE_NAME)

        # we only create the mediasite module item, we don't update it
        # TODO: look into whether we should update it
        if mediasite_module_item is None:
            mediasite_module_item = ModuleItem(module_id=mediasite_module.id,
                                               title=CanvasAPI.MEDIASITE_MODULE_ITEM_NAME,
                                               type=CanvasAppType.ExternalTool.value,
                                               external_url=external_url,
                                               content_id = external_tool_id)
            mediasite_module_item = CanvasAPI.create_module_item(course_id, mediasite_module_item)

        return mediasite_module_item

    ##########################################################
    # Users, including enrollments
    ##########################################################
    @staticmethod
    def get_enrollments_for_teachers_and_tas(course_id):
        json = CanvasAPI.get_canvas_request(partial_url='courses/{0}/enrollments?type[]={1}&type[]={2}'
                                            .format(course_id, 'TeacherEnrollment', 'TaEnrollment'))
        serializer = EnrollmentSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return [Enrollment(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def get_enrollments(course_id, include_user_email):
        enrollments = CanvasAPI.get_enrollments_for_teachers_and_tas(course_id=course_id)
        # find users for enrollments to add the email address, not available in the
        # enrollments API call, and an expensive call so optional
        if include_user_email:
            for enrollment_counter, enrollment in enumerate(enrollments):
                enrollments[enrollment_counter].user = CanvasAPI.get_user_profile(enrollment.user.id)
        return enrollments

    @staticmethod
    def get_user_profile(user_id):
        json = CanvasAPI.get_canvas_request(partial_url='users/{0}/profile'.format(user_id))
        serializer = UserSerializer(data=json)
        validated = serializer.is_valid()
        if validated:
            return User(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def get_teaching_users_for_course(course_id):
        json = CanvasAPI.get_canvas_request(partial_url='courses/{0}/users?enrollment_type=teacher&include[]=email'
                                            .format(course_id))
        serializer = UserSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return [User(**attr) for attr in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def get_ta_users_for_course(course_id):
        json = CanvasAPI.get_canvas_request(partial_url='courses/{0}/users?enrollment_type=ta&include[]=email'
                                            .format(course_id))
        serializer = UserSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return [User(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

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
    @staticmethod
    def get_canvas_request(partial_url):
        r = requests.get(url=CanvasAPI.get_canvas_url(partial_url),
                         headers = CanvasAPI.get_canvas_headers())
        return r.json()

    @staticmethod
    def post_canvas_request(partial_url, data):
        r = requests.post(url = CanvasAPI.get_canvas_url(partial_url),
                          data=json.dumps(data),
                          headers = CanvasAPI.get_canvas_headers())
        return r.json()

    @staticmethod
    def get_canvas_url(partial_url):
        # TODO: make canvas URL a configuration parameter
        if CanvasAPI.is_test():
            return 'https://harvard.test.instructure.com/api/v1/{0}'.format(partial_url)
        elif CanvasAPI.is_production():
            return 'https://canvas.harvard.edu/api/v1/{0}'.format(partial_url)
        else:
            return 'https://canvas-sandbox.tlt.harvard.edu/api/v1/{0}'.format(partial_url)

    @staticmethod
    def get_canvas_headers():
        # TODO: pull user_token from secure store
        # default to sandbox user_token
        user_token = 'OPMm7g8AAISwhGh0cS8Vn6pnKmsJBwFSHzsnAMCRAf4btYzmJtXUShjnGFDsUCET'
        if CanvasAPI.is_test():
            user_token = '1875~iZCoAtRqWworZTwz0GdrvLgSFdv01j6so5oa7Uuxt8JRi2y7aq3x7ydyFzvQpXMM'
        elif CanvasAPI.is_production():
            user_token = '1875~Op1MVZaDnZn8nAHB4eJsRda2YkYHdJKIHxNe0mry09Xnug9gS5qZVGkXUCNn1bD2'
        return {'Authorization': 'Bearer ' + user_token, 'Content-Type': 'application/json'}

    @staticmethod
    def is_production():
        return False

    @staticmethod
    def is_test():
        return True
