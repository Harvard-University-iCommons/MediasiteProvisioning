from django.test import TestCase
from .apimethods import CanvasAPI

# Create your tests here.
class CanvasAPITest(TestCase):

    def test_get_accounts_for_current_user(self):
        accounts = CanvasAPI.get_accounts_for_current_user()
        self.assertFalse(accounts is None)
