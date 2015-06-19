from django.test import TestCase
from .apimethods import CanvasAPI

# Create your tests here.
class CanvasAPITest(TestCase):

    def test_getting_course_hiearchy(self):
        accounts = CanvasAPI.get_accounts_for_current_user()
        self.assertFalse(accounts is None)

        if len(accounts) > 0:
            account = accounts[0]
            courses_for_account = CanvasAPI.get_courses_for_account(account.id)
            self.assertFalse(courses_for_account is None)
            if len(courses_for_account) > 0:
                course_to_test = courses_for_account[0]

                course = CanvasAPI.get_course(course_to_test.id)
                self.assertFalse(course is None)
                teachers = CanvasAPI.get_enrollments(course_id=course.id, include_user_email=True)
                self.assertFalse(teachers is None)
