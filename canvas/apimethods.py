import requests
from .serializer import AccountSerializer, CourseSerializer, EnrollmentSerializer, UserSerializer, ModuleSerializer
from .serializer import ModuleItemSerializer
from .apimodels import Course, Module, ModuleItem, Account, User

class CanvasAPI:
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

    ##########################################################
    # Courses
    ##########################################################
    @staticmethod
    def search_courses(account_id, search_term):
        json = CanvasAPI.get_canvas_request(
            partial_url='accounts/{0}/courses?search_term={1}&include=term'.format(account_id, search_term))
        serializer = CourseSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            search_results = [Course(**attrs) for attrs in serializer.validated_data]
            for n, course in enumerate(search_results):
                # update the enrollment data which is not pulled by the search API
                if False:
                    course.enrollments = CanvasAPI.get_enrollments(course_id=course.id, update_user_email=False)

                # get the teaching users
                course.teaching_users = CanvasAPI.get_teaching_users_for_course(course.id)

                # get the Mediasite module
                course.canvas_mediasite_module_item = CanvasAPI.get_mediasite_module_item(course.id)

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
        return CanvasAPI.post_canvas_request(partial_url='courses{0}/modules'.format(course_id), data = module)

    @staticmethod
    def get_module(course_id, module_name):
        return filter(lambda x: x.name == module_name, CanvasAPI.get_modules(course_id)).__next__()

    @staticmethod
    def get_or_create_module(course_id, module_name):
        module = CanvasAPI.get_module(course_id, module_name)
        if module is None:
            module = CanvasAPI.create_module(course_id, module_name)
        # TODO: make sure there is only one module of this name
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
    def get_module_item(course_id, module_id, title, type):
        module_items = CanvasAPI.get_module_items(course_id, module_id)
        return filter(lambda x: x.title == title and x.type == type, module_items).__next__()

    @staticmethod
    def get_mediasite_module_item(course_id):
        mediasite_module = CanvasAPI.get_module(course_id, module_name='Mediasite')
        if mediasite_module is not None and mediasite_module.items_count > 0:
            return CanvasAPI.get_module_item(course_id, mediasite_module.id, title='Course Lecture Video', type='ExternalTool')

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
            return [User(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def get_enrollments(course_id, update_user_email):
        enrollments = CanvasAPI.get_enrollments_for_teachers_and_tas(course_id=course_id)
        # find users for enrollments to add the email address, not available in the
        # enrollments API call
        if update_user_email:
            for enrollment_counter, enrollment in enumerate(enrollments):
                enrollments[enrollment_counter]['user'] = CanvasAPI.get_user_profile(enrollment['user']['id'])
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
    # API methods
    ##########################################################
    @staticmethod
    def get_canvas_request(partial_url):
        r = requests.get(url= CanvasAPI.get_canvas_url(partial_url), headers = CanvasAPI.get_canvas_headers())
        return r.json()

    @staticmethod
    def post_canvas_request(partial_url, data):
        r = requests.post(url = CanvasAPI.get_canvas_url(partial_url), data=data,
                          headers = CanvasAPI.get_canvas_headers())

    @staticmethod
    def get_canvas_url(partial_url):
        # TODO: make canvas URL a configuration parameter
        if CanvasAPI.is_production():
            return 'https://canvas.harvard.edu/api/v1/{0}'.format(partial_url)
        else:
            return 'https://canvas-sandbox.tlt.harvard.edu/api/v1/{0}'.format(partial_url)

    @staticmethod
    def get_canvas_headers():
        # TODO: pull user_token from secure store
        # default to sandbox user_token
        user_token = 'OPMm7g8AAISwhGh0cS8Vn6pnKmsJBwFSHzsnAMCRAf4btYzmJtXUShjnGFDsUCET'
        if CanvasAPI.is_production():
            user_token = '1875~Op1MVZaDnZn8nAHB4eJsRda2YkYHdJKIHxNe0mry09Xnug9gS5qZVGkXUCNn1bD2'
        return {'Authorization': 'Bearer ' + user_token}

    @staticmethod
    def is_production():
        return False
