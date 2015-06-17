import requests
import json
from requests.auth import HTTPBasicAuth

from .serializer import FolderSerializer, FolderPermissionSerializer, HomeSerializer
from .apimodels import Home, Folder


class MediasiteAPI:
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
                # TODO: this may work, but could be cleaned up
                return [Folder(**attrs) for attrs in serializer.validated_data][0]
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

    def get_mediasite_request(url):
        return MediasiteAPI.mediasite_request(url=url, method='GET', body=None)

    def post_mediasite_request(url, body):
        return MediasiteAPI.mediasite_request(url=url, method='POST', body=body)

    def mediasite_request(url, method, body):
        #url = 'https://dvsdev.mediasite.video.harvard.edu/mediasite/api/v1/' + url
        url = 'https://sandbox.mediasite.video.harvard.edu/mediasite/api/v1/' + url
        auth = HTTPBasicAuth('Nick_Carmello', 'daft-jaggy-beauty')
        #api_key = '4746f072-7faa-4b91-8fdf-3b3aca910c26'
        api_key = 'e368e3bb-4a6a-48a7-af17-a868300c6d63'

        headers = {'sfapikey': api_key, 'Content-Type': 'application/json'}
        if method == 'POST':
            r = requests.post(url=url, auth=auth, headers=headers, data=json.dumps(body), verify=False)
        else:
            r = requests.get(url=url, auth=auth, headers=headers, verify=False)
        return r.json()




