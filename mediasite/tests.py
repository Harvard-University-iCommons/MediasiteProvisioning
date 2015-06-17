from django.test import TestCase
from .apimethods import MediasiteAPI

# Create your tests here.
class MediasiteTestCase(TestCase):

    def test_can_connect_to_Mediasite_home(self):
        root_folder_id = MediasiteAPI.get_root_folder_id()
        self.assertFalse(root_folder_id is None)

    def test_create_folder_hierarchy(self):
        course_folder = None
        proof_of_concept_root_folder = MediasiteAPI.get_or_create_folder('ProofOfConcept', parent_folder_id=None)
        self.assertFalse(proof_of_concept_root_folder is None)
        year_folder = MediasiteAPI.get_or_create_folder('2015', parent_folder_id=proof_of_concept_root_folder.Id)
        self.assertFalse(year_folder is None)
        term_folder = MediasiteAPI.get_or_create_folder('Winter', parent_folder_id=year_folder.Id)
        self.assertFalse(term_folder is None)
        course_folder = MediasiteAPI.get_or_create_folder('BIO-212', parent_folder_id=term_folder.Id)
        self.assertFalse(course_folder is None)