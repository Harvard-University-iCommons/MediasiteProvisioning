import requests
from .serializer import AccountSerializer, CourseSerializer
from .apimodels import Account, Course

class CanvasAPI:
    @staticmethod
    def get_accounts_for_current_user():
        json = CanvasAPI.get_canvas_request(partial_url='accounts')
        serializer = AccountSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return serializer.data
        else:
            errors = serializer.errors

    @staticmethod
    def search_courses(account_id, search_term):
        json = CanvasAPI.get_canvas_request(partial_url='accounts/{0}/courses?search_term={1}&include=term'.format(account_id, search_term))
        serializer = CourseSerializer(data=json, many=True)
        validated = serializer.is_valid()
        if validated:
            return serializer.data
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