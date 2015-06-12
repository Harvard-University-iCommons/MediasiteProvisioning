import requests
from .serializer import AccountSerializer, CourseSerializer, EnrollmentSerializer, UserSerializer
from .apimodels import Course


class CanvasAPI:
    @staticmethod
    def get_accounts_for_current_user():
        json = CanvasAPI.get_canvas_request(partial_url='accounts')
        serializer = AccountSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            serializer.save()
            return serializer.validated_data
        else:
            errors = serializer.errors

    @staticmethod
    def search_courses(account_id, search_term):
        json = CanvasAPI.get_canvas_request(
            partial_url='accounts/{0}/courses?search_term={1}&include=term'.format(account_id, search_term))
        serializer = CourseSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return serializer.validated_data
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
            return serializer.validated_data
        else:
            errors = serializer.errors

    @staticmethod
    def get_enrollments_for_teachers_and_tas(course_id):
        json = CanvasAPI.get_canvas_request(partial_url='courses/{0}/enrollments?type[]={1}&type[]={2}'
                                            .format(course_id, 'TeacherEnrollment', 'TaEnrollment'))
        serializer = EnrollmentSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return serializer.validated_data
        else:
            errors = serializer.errors

    @staticmethod
    def get_user_profile(user_id):
        json = CanvasAPI.get_canvas_request(partial_url='users/{0}/profile'.format(user_id))
        serializer = UserSerializer(data=json)
        validated = serializer.is_valid()
        if validated:
            return serializer.validated_data
        else:
            errors = serializer.errors

    @staticmethod
    def get_teaching_users_for_course(course_id):
        json = CanvasAPI.get_canvas_request(partial_url='courses/{0}/users?enrollment_type=teacher&include[]=email'.format(course_id))
        serializer = UserSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return serializer.validated_data
        else:
            errors = serializer.errors

    @staticmethod
    def get_ta_users_for_course(course_id):
        json = CanvasAPI.get_canvas_request(partial_url='courses/{0}/users?enrollment_type=ta&include[]=email'.format(course_id))
        serializer = UserSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return serializer.validated_data
        else:
            errors = serializer.errors

    @staticmethod
    def get_canvas_request(partial_url):
        # TODO: pull user_token from secure store
        user_token = '1875~Op1MVZaDnZn8nAHB4eJsRda2YkYHdJKIHxNe0mry09Xnug9gS5qZVGkXUCNn1bD2'
        # TODO: make canvas URL a configuration parameter
        url = 'https://canvas.harvard.edu/api/v1/' + partial_url
        headers = {'Authorization': 'Bearer ' + user_token}
        r = requests.get(url, headers = headers)
        return r.json()