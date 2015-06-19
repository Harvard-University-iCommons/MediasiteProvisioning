from django.test import TestCase
from .apimethods import MediasiteAPI
from .apimodels import Role, Folder

# Create your tests here.
class MediasiteTestCase(TestCase):

    def test_can_connect_to_Mediasite_home(self):
        root_folder_id = MediasiteAPI.get_root_folder_id()
        self.assertFalse(root_folder_id is None)

    def test_create_and_destroy_folders(self):
        root_folder_name = "ProofOfConcept"
        term_name = "Winter"
        course_name = "EPI201-01"
        year_name = "2015"
        course_sis_id = "346889"
        course_code = "Advanced Epidemiologic Methods"
        oath_consumer_key = "canvas_proof_of_concept"

        course_folder = None
        proof_of_concept_root_folder = MediasiteAPI.get_or_create_folder(root_folder_name, parent_folder_id=None)
        self.assertFalse(proof_of_concept_root_folder is None)
        year_folder = MediasiteAPI.get_or_create_folder(year_name, parent_folder_id=proof_of_concept_root_folder.Id)
        self.assertFalse(year_folder is None)
        term_folder = MediasiteAPI.get_or_create_folder(term_name, parent_folder_id=year_folder.Id)
        self.assertFalse(term_folder is None)
        course_folder = MediasiteAPI.get_or_create_folder(course_name, parent_folder_id=term_folder.Id)
        self.assertFalse(course_folder is None)

        catalog_name = "({0}) {1} {2} ({3})".format(term_name, course_name, course_code, course_sis_id)
        course_catalog = MediasiteAPI.get_or_create_catalog(catalog_name, course_folder.Id)
        self.assertFalse(course_catalog is None)

        role_name = "{0}@{1}".format(course_name, oath_consumer_key)
        course_role = MediasiteAPI.get_or_create_role(role_name)
        self.assertFalse(course_role is None)

        folder_permissions = MediasiteAPI.get_folder_permissions(course_folder.Id)
        folder_permissions = MediasiteAPI.update_folder_permissions(
            folder_permissions, course_role, MediasiteAPI.READ_ONLY_PERMISSION_FLAG)
        self.assertFalse(folder_permissions is None)

        # Remove permissions for authenticated users
        authenticated_user_role = MediasiteAPI.get_role("AuthenticatedUsers")
        folder_permissions = MediasiteAPI.update_folder_permissions(
            folder_permissions, authenticated_user_role, MediasiteAPI.NO_ACCESS_PERMISSION_FLAG)

        # Make sure that Gregory_Carpenter@harvard.edu has editor role
        greg = MediasiteAPI.get_user_by_email_address("gregory_carpenter@harvard.edu")
        if greg is not None:
            folder_permissions = MediasiteAPI.update_folder_permissions(
                folder_permissions,
                Role(Id = MediasiteAPI.convert_user_profile_to_role_id(greg.Id)),
                MediasiteAPI.READ_WRITE_PERMISSION_FLAG)

        #Assign permissions to folder
        MediasiteAPI.assign_permissions_to_folder(course_folder.Id, folder_permissions)
