import requests
import json
import uuid
import urllib
import logging
import time

from django.conf import settings
from requests.auth import HTTPBasicAuth

from .serializer import (
    CatalogSerializer,
    FolderSerializer,
    HomeSerializer,
    ModuleSerializer,
    ResourcePermissionSerializer,
    RoleSerializer,
    UserProfileSerializer, )
from .apimodels import (
    AccessControl,
    Catalog,
    Folder,
    FolderPermission,
    Home,
    Module,
    ResourcePermission,
    Role,
    UserProfile, )
from .utils import odata_encode_str

logger = logging.getLogger(__name__)


class MediasiteServiceException(Exception):
    _mediasite_exception = None

    def __init__(self, mediasite_exception,
                 message='Error communicating with Mediasite.  Please note this error and contact support.'):
        super(MediasiteServiceException, self).__init__(message)
        self._mediasite_exception=mediasite_exception

    def status_code(self):
        if self._mediasite_exception:
            if hasattr(self._mediasite_exception, 'response'):
                return self._mediasite_exception.response.status_code

    def server_error(self):
        if self._mediasite_exception:
            if hasattr(self._mediasite_exception, 'response'):
                try:
                    error = self._mediasite_exception.response.json()['odata.error']['message']['value']
                except:
                    error = 'Could not extract error from server'
                    pass
                return error

class MediasiteAPI:
    VIEW_ONLY_PERMISSION_FLAG = 4
    READ_ONLY_PERMISSION_FLAG = 5
    READ_WRITE_PERMISSION_FLAG = 7
    NO_ACCESS_PERMISSION_FLAG = 0

    DEFAULT_TERM_NAME = 'Default Term'

    ######################################################
    # Folders
    ######################################################
    _root_folder_id = None

    @staticmethod
    def get_root_folder_id():
        if MediasiteAPI._root_folder_id is None:
            url = 'Home'
            json =  MediasiteAPI.get_mediasite_request_json(url)
            serializer = HomeSerializer(data=json)
            if serializer.is_valid(raise_exception=True):
                MediasiteAPI._root_folder_id = Home(**serializer.validated_data).RootFolderId
        return MediasiteAPI._root_folder_id

    @staticmethod
    def get_folder(name, parent_folder_id, alternative_search_term=None):
        folders = MediasiteAPI.get_folders(name, parent_folder_id)
        folder = next((f for f in folders if f.Name == name), None)
        # 8/25/16 JDB: NOTE - The folder searches are exact match, so using an alternative of the sis id seems
        # wasteful and a potential problem for legacy naming schemes.  Commenting this out for now.
        # the folder name can be too long for the API to parse, so we can use an alternate unique search term
        # ideally the course sis id
        # if not folder and alternative_search_term is not None:
        #     folders = MediasiteAPI.get_folders(alternative_search_term, parent_folder_id)
        #     folder = next((f for f in folders if f.Name == name), None)
        return folder

    @staticmethod
    def get_folders(name, parent_folder_id):
        if parent_folder_id is None:
            parent_folder_id = MediasiteAPI.get_root_folder_id()
        # we only search on the first 40 characters of the folder name because the API does not seem able to process
        # longer strings
        encoded_name = odata_encode_str(name)
        url = 'Folders'
        params='$filter=ParentFolderId eq \'{0}\' and Name eq \'{1}\''.format(parent_folder_id, encoded_name)
        json = MediasiteAPI.get_mediasite_request_json(url, params=params)
        # the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json
        serializer = FolderSerializer(data=json['value'], many=True)
        if serializer.is_valid(raise_exception=True):
            return [Folder(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def create_folder(name, parent_folder_id, is_copy_destination=False, is_shared=False):
        folder_to_create = dict(
            Name=name,
            ParentFolderId=parent_folder_id,
            IsReviewEditApproveEnabled=False,
            IsCopyDestination=is_copy_destination,
            IsShared=is_shared
        )
        json = MediasiteAPI.post_mediasite_request_json('Folders', body=folder_to_create)
        serializer = FolderSerializer(data=json)
        if serializer.is_valid(raise_exception=True):
            return Folder(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def get_or_create_folder(name, parent_folder_id, alternate_search_term=None, is_copy_destination=False, is_shared=False):
        if parent_folder_id is None:
            parent_folder_id = MediasiteAPI.get_root_folder_id()
        if parent_folder_id is not None:
            folder = MediasiteAPI.get_folder(name, parent_folder_id, alternate_search_term)
            if not folder:
                folder = MediasiteAPI.create_folder(name, parent_folder_id, is_copy_destination, is_shared)
        return folder

    ######################################################
    # Catalogs
    ######################################################
    @staticmethod
    def get_or_create_catalog(friendly_name, catalog_name, course_folder_id, alternative_search_term):
        catalog = MediasiteAPI.get_catalog(catalog_name, course_folder_id, alternative_search_term)
        if catalog is None:
            catalog = MediasiteAPI.create_catalog(friendly_name, catalog_name, course_folder_id)
        return catalog

    @staticmethod
    def get_catalog(name, course_folder_id, alternative_search_term):
        catalogs = MediasiteAPI.get_catalogs(name)
        catalog = next((c for c in catalogs if c.LinkedFolderId == course_folder_id), None)
        # 8/25/16 JDB: NOTE - commenting this out as I don't think we need to search on an alternative name or
        # even match on name at all.  There should only be one catalog linked to a course folder in this
        # provisioning setup.
        # if not catalog and len(name) > 40:
        #     catalogs = MediasiteAPI.get_catalogs(alternative_search_term)
        #     catalog = next((c for c in catalogs if c.LinkedFolderId == course_folder_id and c.Name == name), None)
        return catalog

    @staticmethod
    def get_catalogs(name):
        url = 'Catalogs'
        encoded_name = odata_encode_str(name)
        params='$filter=Name eq \'{0}\''.format(encoded_name)
        json = MediasiteAPI.get_mediasite_request_json(url, params=params)
        serializer = CatalogSerializer(data=json['value'], many=True)
        if serializer.is_valid(raise_exception=True):
            return [Catalog(**attrs) for attrs in serializer.validated_data]
        else:
            errors = serializer.errors

    @staticmethod
    def create_catalog(friendly_name, catalog_name, course_folder_id):
        catalog_to_create = dict(
            FriendlyName=friendly_name,
            Name = catalog_name,
            LinkedFolderId = course_folder_id
        )
        json = MediasiteAPI.post_mediasite_request_json('Catalogs', catalog_to_create)
        serializer = CatalogSerializer(data=json)
        if serializer.is_valid(raise_exception=True):
            return Catalog(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def set_catalog_settings(catalog_id, show_date, show_time, items_per_page):
        catalog_settings = dict(
            ShowTablePresentationDate= show_date,
            ShowTablePresentationTime = show_time,
            ShowCardPresentationDate = show_date,
            ShowCardPresentationTime = show_time,
            PresentationsPerPage = items_per_page,
            AllowLoginControls = False
        )
        url = 'Catalogs(\'{0}\')/Settings'.format(catalog_id)
        MediasiteAPI.patch_mediasite_request(url, catalog_settings)

    ######################################################
    # Modules
    ######################################################
    @staticmethod
    def get_or_create_module(module_id, name, catalog_mediasite_id=None):
        module = MediasiteAPI.get_module(module_id=module_id)
        if module is None:
            module = MediasiteAPI.create_module(
                module_id, name, catalog_mediasite_id)
        return module

    @staticmethod
    def create_module(module_id, name, catalog_mediasite_id=None):
        module_to_create = dict(ModuleId=module_id, Name=name)
        if catalog_mediasite_id:
            # immediately associate the module with a catalog
            module_to_create['Associations'] = [catalog_mediasite_id]
        module_json = MediasiteAPI.post_mediasite_request_json('Modules',
                                                               module_to_create)
        serializer = ModuleSerializer(data=module_json)
        if serializer.is_valid(raise_exception=True):
            return Module(**serializer.validated_data)

    @staticmethod
    def get_module(mediasite_id=None, module_id=None):
        """
        Gets a module by either its Id or ModuleId properties.
        :param mediasite_id: The module's Id property.
        :param module_id: The module's ModuleId property.
        :return: a mediasite.apimodels.Module if found; None if no object found;
         throws an error if multiple objects found.
        """
        if not(bool(mediasite_id) ^ bool(module_id)):  # xor
            raise ValueError('get_module() requires one identifier')
        return MediasiteAPI.get_module_by_mediasite_id(mediasite_id) \
            if mediasite_id else MediasiteAPI.get_module_by_module_id(module_id)

    @staticmethod
    def get_module_by_mediasite_id(mediasite_id):
        """
        Finds a module by its Id.
        :return: a mediasite.apimodels.Module if found; None if no object found.
        """
        url = "Modules('{}')".format(mediasite_id)
        try:
            module_json = MediasiteAPI.get_mediasite_request_json(url)
        except MediasiteServiceException as mse:
            if mse.status_code() == requests.codes.not_found:
                return None
            raise mse
        serializer = ModuleSerializer(data=module_json)
        if serializer.is_valid(raise_exception=True):
            return Module(**serializer.validated_data)

    @staticmethod
    def get_module_by_module_id(module_id):
        """
        Finds a module by its ModuleId. Expects only one module to match.
        :return: a mediasite.apimodels.Module if found; None if no object found;
         throws an error if multiple objects found.
        """
        url = 'Modules'
        encoded_module_id = odata_encode_str(module_id)
        # this is equivalent to a 'contains' search, as this is a
        # mediasite-search-backed filter endpoint
        params = "$filter=ModuleId eq '{0}'".format(encoded_module_id)
        module_json = MediasiteAPI.get_mediasite_request_json(url, params=params)
        if module_json['odata.count'] == "0":
            return None
        if module_json['odata.count'] != "1":
            raise ValueError(('get_module_by_module_id() found more than one '
                              'Module for filter params {}').format(params))
        serializer = ModuleSerializer(data=module_json['value'], many=True)
        if serializer.is_valid(raise_exception=True):
            return Module(**serializer.validated_data[0])

    @staticmethod
    def add_module_association_by_mediasite_id(module_mediasite_id,
                                               associated_mediasite_id):
        """
        Creates an association between a module and a catalog. Note: if the
        association already exists, no error is returned, and the association
        is retained.
        :param module_mediasite_id: The Module's Id property.
        :param associated_mediasite_id: The Catalog's Id property.
        :return: the requests.Response of the mediasite API call (status code
         will be 204 No Content if the association was created or already
         existed).
        """
        url = "Modules('{}')/AddAssociation".format(module_mediasite_id)
        associated_object = dict(MediasiteId=associated_mediasite_id)
        return MediasiteAPI.mediasite_request(url, 'POST', associated_object)

    ######################################################
    # Permissions
    ######################################################
    @staticmethod
    def get_resource_permissions(folder_id):
        url = 'ResourcePermissions(\'{0}\')'.format(folder_id)
        json = MediasiteAPI.get_mediasite_request_json(url)
        # the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json
        serializer = ResourcePermissionSerializer(data=json)
        if serializer.is_valid(raise_exception=True):
            return ResourcePermission(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def assign_permissions_to_folder(folder_id, folder_permissions):
        url = 'Folders(\'{0}\')/UpdatePermissions'.format(folder_id)
        # Need to change the folder_permissions object into a dictionary object that can be cast to json
        # when posting to the Mediasite API
        folder_permissions_as_dict = folder_permissions.__dict__
        folder_permissions_as_dict['Permissions'] = [ac.__dict__ for ac in folder_permissions.Permissions]
        # this call returns a status object that is probably of no use to us
        MediasiteAPI.post_mediasite_request_json(url, body=folder_permissions_as_dict)

    @staticmethod
    def get_folder_permissions(folder_id):
        folder_permissions = FolderPermission()
        permissions_for_folder = MediasiteAPI.get_resource_permissions(folder_id)
        if permissions_for_folder is not None:
            folder_permissions.Owner = permissions_for_folder.Owner
            folder_permissions.Permissions = permissions_for_folder.AccessControlList
        return folder_permissions

    @staticmethod
    def update_folder_permissions(folder_permissions, role, permission_mask):
        existing_permission = next((fp for fp in folder_permissions.Permissions if fp.RoleId == role.Id), None)
        if existing_permission is not None:
            if permission_mask == MediasiteAPI.NO_ACCESS_PERMISSION_FLAG:
                folder_permissions.Permissions = [fp for fp in folder_permissions.Permissions if fp.RoleId != role.Id]
            else:
                existing_permission.PermissionMask = permission_mask
        elif permission_mask != MediasiteAPI.NO_ACCESS_PERMISSION_FLAG:
            folder_permissions.Permissions.append(
                AccessControl(RoleId = role.Id, PermissionMask = permission_mask)
            )
        return folder_permissions

    ######################################################
    # Roles
    ######################################################
    @staticmethod
    def create_role(role_name, directory_entry):
        role_to_create = dict(
            Name = role_name,
            DirectoryEntry = directory_entry
        )
        json = MediasiteAPI.post_mediasite_request_json('Roles', body=role_to_create)
        serializer = RoleSerializer(data=json)
        if serializer.is_valid(raise_exception=True):
            return Role(**serializer.validated_data)
        else:
            errors = serializer.errors

    @staticmethod
    def get_role_by_name(role_name):
        url = 'Roles'
        encoded_name = odata_encode_str(role_name)
        params = '$filter=Name eq \'{0}\''.format(encoded_name)
        json = MediasiteAPI.get_mediasite_request_json(url, params=params)
        # the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json
        serializer = RoleSerializer(data=json['value'], many=True)
        if serializer.is_valid(raise_exception=True):
            roles = [Role(**attrs) for attrs in serializer.validated_data]
            if len(roles) == 1:
                return roles[0]
        else:
            errors = serializer.errors

    @staticmethod
    def get_role_by_directory_entry(directory_entry):
        url = 'Roles'
        encoded_dir_entry = odata_encode_str(directory_entry)
        params='$filter=DirectoryEntry eq \'{0}\''.format(encoded_dir_entry)
        json = MediasiteAPI.get_mediasite_request_json(url, params=params)
        # the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json
        serializer = RoleSerializer(data=json['value'], many=True)
        if serializer.is_valid(raise_exception=True):
            roles = [Role(**attrs) for attrs in serializer.validated_data]
            if len(roles) == 1:
                return roles[0]
        else:
            errors = serializer.errors

    @staticmethod
    def get_or_create_role(role_name, directory_entry):
        role = MediasiteAPI.get_role_by_directory_entry(directory_entry)
        if role is None:
            role = MediasiteAPI.get_role_by_name(role_name)
            if role is None:
                role = MediasiteAPI.create_role(role_name, directory_entry)
            elif role.DirectoryEntry != directory_entry:
                raise Exception('A role with the name {0} already exists, but it has a '
                                'different directory entry [{1}].  Provisioning cannot '
                                'continue until this role is manually deleted'.format(role_name, role.DirectoryEntry));
                # TODO: if Mediasite ever allows us to delete or update a role.
                # MediasiteAPI.delete_role(role);
                # role = MediasiteAPI.create_role(role_name, directory_entry);
        return role

    ######################################################
    # User Profiles
    ######################################################
    @staticmethod
    def get_user_by_email_address(email_address):
        url = 'UserProfiles'
        encoded_email = odata_encode_str(email_address)
        params='$filter=endswith(Email, \'{0}\')'.format(encoded_email)
        json = MediasiteAPI.get_mediasite_request_json(url, params=params)
        # the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json
        serializer = UserProfileSerializer(data=json['value'], many=True)
        if serializer.is_valid(raise_exception=True):
            user_profiles = [UserProfile(**attrs) for attrs in serializer.validated_data]
            if len(user_profiles) == 1:
                return user_profiles[0]
        else:
            errors = serializer.errors

    @staticmethod
    def create_user(user):
        url = 'UserProfiles'
        json = MediasiteAPI.post_mediasite_request_json(url=url, body=user.__dict__)
        serializer = UserProfileSerializer(data=json)
        if serializer.is_valid(raise_exception=True):
            return UserProfile(**serializer.validated_data)

    @staticmethod
    def convert_user_profile_to_role_id(user_profile_id):
        return str(uuid.UUID(user_profile_id[:32]))

    ######################################################
    # Generic API Methods
    ######################################################
    @staticmethod
    def get_mediasite_request_json(url, params=None):
        return MediasiteAPI.mediasite_request_json(url=url, method='GET', body=None, params=params)

    @staticmethod
    def post_mediasite_request_json(url, body):
        return MediasiteAPI.mediasite_request_json(url=url, method='POST', body=body)

    @staticmethod
    def put_mediasite_request_json(url, body):
        return MediasiteAPI.mediasite_request_json(url=url, method='PUT', body=body)

    @staticmethod
    def patch_mediasite_request_json(url, body):
        return MediasiteAPI.mediasite_request_json(url=url, method='PATCH', body=body)

    @staticmethod
    def patch_mediasite_request(url, body):
        return MediasiteAPI.mediasite_request(url=url, method='PATCH', body=body)

    @staticmethod
    def mediasite_request(url, method, body, params=None):
        start_time = time.time()
        try:
            if method == 'POST':
                r = requests.post(url=MediasiteAPI.get_mediasite_url(url),
                                  auth=MediasiteAPI.get_mediasite_auth(),
                                  headers=MediasiteAPI.get_mediasite_headers(),
                                  data=json.dumps(body))
            elif method == 'PUT':
                r = requests.put(url=MediasiteAPI.get_mediasite_url(url),
                                 auth=MediasiteAPI.get_mediasite_auth(),
                                 headers=MediasiteAPI.get_mediasite_headers(),
                                 data=json.dumps(body))
            elif method == 'DELETE':
                r = requests.delete(url=MediasiteAPI.get_mediasite_url(url),
                                    auth=MediasiteAPI.get_mediasite_auth(),
                                    headers=MediasiteAPI.get_mediasite_headers(),
                                    data=json.dumps(body))
            elif method == 'PATCH':
                r = requests.patch(url=MediasiteAPI.get_mediasite_url(url),
                                   auth=MediasiteAPI.get_mediasite_auth(),
                                   headers=MediasiteAPI.get_mediasite_headers(),
                                   data=json.dumps(body))
            else:
                r = requests.get(url=MediasiteAPI.get_mediasite_url(url),
                                 params=params,
                                 auth=MediasiteAPI.get_mediasite_auth(),
                                 headers=MediasiteAPI.get_mediasite_headers())
            r.raise_for_status()
        except Exception as e:
            elapsed_secs = time.time() - start_time
            logger.info("tried to make a {} call to {} via requests in "
                        "{:.3f}s".format(method, url, elapsed_secs))
            raise MediasiteServiceException(mediasite_exception=e)

        elapsed_secs = time.time() - start_time
        logger.debug("made a {} call to {} via requests in {:.3f}s".format(
            r.request.method, r.request.url, elapsed_secs))
        return r

    @staticmethod
    def mediasite_request_json(url, method, body, params=None):
        req = MediasiteAPI.mediasite_request(url, method, body, params)
        try:
            return req.json()
        except Exception as e:
            raise MediasiteServiceException(mediasite_exception=e)

    @staticmethod
    def get_mediasite_auth():
        return HTTPBasicAuth(settings.MEDIASITE_USERNAME, settings.MEDIASITE_PASSWORD)

    @staticmethod
    def get_mediasite_headers():
        api_key = settings.MEDIASITE_API_KEY
        return {'sfapikey': api_key, 'Content-Type': 'application/json'}

    @staticmethod
    def get_mediasite_url(partial_url):
        return settings.MEDIASITE_URL.format(partial_url)

    @staticmethod
    def is_production():
        return False
        # return settings.DEBUG == False
