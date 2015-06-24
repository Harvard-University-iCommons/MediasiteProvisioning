import requests
import json
import uuid
from requests.auth import HTTPBasicAuth

from .serializer import FolderSerializer, FolderPermissionSerializer, HomeSerializer, CatalogSerializer
from .serializer import RoleSerializer, ResourcePermissionSerializer, FolderPermissionSerializer
from .serializer import UserProfileSerializer
from .apimodels import Home, Folder, Catalog, Role, ResourcePermission, FolderPermission, AccessControl, UserProfile


class MediasiteAPI:
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
            json =  MediasiteAPI.get_mediasite_request(url)
            serializer = HomeSerializer(data=json)
            if serializer.is_valid():
                MediasiteAPI._root_folder_id = Home(**serializer.validated_data).RootFolderId
        return MediasiteAPI._root_folder_id

    @staticmethod
    def get_folder(name, parent_folder_id):
        if parent_folder_id is None:
            parent_folder_id = MediasiteAPI.get_root_folder_id()
        url = 'Folders?$filter=ParentFolderId eq \'{0}\' and Name eq \'{1}\''.format(parent_folder_id, name)
        json = MediasiteAPI.get_mediasite_request(url)
        # TODO: the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json, but this is not a generally good approach
        if json['odata.count'] == '1':
            serializer = FolderSerializer(data=json['value'], many=True)
            if serializer.is_valid():
                folders = [Folder(**attrs) for attrs in serializer.validated_data]
                if len(folders) == 1:
                    return folders[0]
            else:
                errors = serializer.errors

    @staticmethod
    def create_folder(name, parent_folder_id):
        folder_to_create = dict(
            Name = name,
            ParentFolderId = parent_folder_id
        )
        json = MediasiteAPI.post_mediasite_request('Folders', body=folder_to_create)
        serializer = FolderSerializer(data=json)
        if serializer.is_valid():
            return Folder(**serializer.validated_data)
        else:
            errors = serializer.errors

    # TODO: the default value of the optional ParentFolderId parameter is hard coded to a value
    # known to be the root folder id of the harvard sandbox.  This is not suitable for production
    # and a means to find the root folder id will need to be part of the code solution
    @staticmethod
    def get_or_create_folder(name, parent_folder_id):
        if parent_folder_id is None:
            parent_folder_id = MediasiteAPI.get_root_folder_id()
        folder = MediasiteAPI.get_folder(name, parent_folder_id)
        if not folder:
            folder = MediasiteAPI.create_folder(name, parent_folder_id)
        return folder

    ######################################################
    # Catalogs
    ######################################################
    @staticmethod
    def get_or_create_catalog(catalog_name, course_folder_id):
        catalog = MediasiteAPI.get_catalog(catalog_name, course_folder_id)
        if catalog is None:
            catalog = MediasiteAPI.create_catalog(catalog_name, course_folder_id)
        return catalog

    @staticmethod
    def get_catalog(catalog_name, course_folder_id):
        url = 'Catalogs?$filter=Name eq \'{0}\''.format(catalog_name)
        json = MediasiteAPI.get_mediasite_request(url)
        # TODO: the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json, but this is not a generally good approach
        if float(json['odata.count']) > 0:
            serializer = CatalogSerializer(data=json['value'], many=True)
            if serializer.is_valid():
                # TODO: this may work, but could be cleaned up
                catalogs = [Catalog(**attrs) for attrs in serializer.validated_data]
                return next((c for c in catalogs if c.LinkedFolderId == course_folder_id), None)
            else:
                errors = serializer.errors

    @staticmethod
    def create_catalog(catalog_name, course_folder_id):
        catalog_to_create = dict(
            Name = catalog_name,
            LinkedFolderId = course_folder_id
        )
        json = MediasiteAPI.post_mediasite_request('Catalogs', catalog_to_create)
        serializer = CatalogSerializer(data=json)
        if serializer.is_valid():
            return Catalog(**serializer.validated_data)
        else:
            errors = serializer.errors

    ######################################################
    # Permissions
    ######################################################
    @staticmethod
    def get_resource_permissions(folder_id):
        url = 'ResourcePermissions(\'{0}\')'.format(folder_id)
        json = MediasiteAPI.get_mediasite_request(url)
        # TODO: the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json, but this is not a generally good approach
        serializer = ResourcePermissionSerializer(data=json)
        if serializer.is_valid():
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
        MediasiteAPI.post_mediasite_request(url, body=folder_permissions_as_dict)

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
        json = MediasiteAPI.post_mediasite_request('Roles', body=role_to_create)
        serializer = RoleSerializer(data=json)
        if serializer.is_valid():
            return Role(**serializer.validated_data)
        else:
            errors = serializer.errors

    # @staticmethod
    # def get_role_by_name(role_name):
    #     url = 'Roles?$filter=Name eq \'{0}\''.format(role_name)
    #     json = MediasiteAPI.get_mediasite_request(url)
    #     # TODO: the json returned is in the oData format, and there do not appear to be any
    #     # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
    #     # underlying json, but this is not a generally good approach
    #     serializer = RoleSerializer(data=json['value'], many=True)
    #     if serializer.is_valid():
    #         roles = [Role(**attrs) for attrs in serializer.validated_data]
    #         if len(roles) == 1:
    #             return roles[0]
    #     else:
    #         errors = serializer.errors

    @staticmethod
    def get_role_by_directory_entry(directory_entry):
        url = 'Roles?$filter=DirectoryEntry eq \'{0}\''.format(directory_entry)
        json = MediasiteAPI.get_mediasite_request(url)
        # TODO: the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json, but this is not a generally good approach
        serializer = RoleSerializer(data=json['value'], many=True)
        if serializer.is_valid():
            roles = [Role(**attrs) for attrs in serializer.validated_data]
            if len(roles) == 1:
                return roles[0]
        else:
            errors = serializer.errors

    @staticmethod
    def get_or_create_role(role_name, directory_entry):
        role = MediasiteAPI.get_role_by_directory_entry(directory_entry)
        if role is None:
            role = MediasiteAPI.create_role(role_name, directory_entry)
        return role

    ######################################################
    # User Profiles
    ######################################################
    @staticmethod
    def get_user_by_email_address(email_address):
        url =  'UserProfiles?$filter=endswith(Email, \'{0}\')'.format(email_address)
        json = MediasiteAPI.get_mediasite_request(url)
        # TODO: the json returned is in the oData format, and there do not appear to be any
        # python libraries that parse oData.  we can extract the 'value' property of the list to get at the
        # underlying json, but this is not a generally good approach
        serializer = UserProfileSerializer(data=json['value'], many=True)
        if serializer.is_valid():
            # TODO: this may work, but could be cleaned up
            user_profiles = [UserProfile(**attrs) for attrs in serializer.validated_data]
            if len(user_profiles) == 1:
                return user_profiles[0]
        else:
            errors = serializer.errors

    @staticmethod
    def create_user(user):
        url = 'UserProfiles'
        json = MediasiteAPI.post_mediasite_request(url=url, body=user.__dict__)
        serializer = UserProfileSerializer(data=json)
        if serializer.is_valid():
            return UserProfile(**serializer.validated_data)

    @staticmethod
    def convert_user_profile_to_role_id(user_profile_id):
        return str(uuid.UUID(user_profile_id[:32]))

    ######################################################
    # Generic API Methods
    ######################################################
    def get_mediasite_request(url):
        return MediasiteAPI.mediasite_request(url=url, method='GET', body=None)

    def post_mediasite_request(url, body):
        return MediasiteAPI.mediasite_request(url=url, method='POST', body=body)

    def mediasite_request(url, method, body):
        url = 'https://dvsdev.mediasite.video.harvard.edu/mediasite/api/v1/' + url
        #url = 'https://sandbox.mediasite.video.harvard.edu/mediasite/api/v1/' + url
        auth = HTTPBasicAuth('Nick_Carmello', 'daft-jaggy-beauty')
        api_key = '4746f072-7faa-4b91-8fdf-3b3aca910c26'
        #api_key = 'e368e3bb-4a6a-48a7-af17-a868300c6d63'

        headers = {'sfapikey': api_key, 'Content-Type': 'application/json'}
        if method == 'POST':
            r = requests.post(url=url, auth=auth, headers=headers, data=json.dumps(body), verify=False)
        else:
            r = requests.get(url=url, auth=auth, headers=headers, verify=False)
        return r.json()