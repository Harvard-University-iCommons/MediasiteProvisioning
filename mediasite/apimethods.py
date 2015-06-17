import requests

from .serializer import FolderSerializer, FolderPermissionSerializer, HomeSerializer


class MediasiteAPI:
    _root_folder_id = None

    @staticmethod
    def get_root_folder_id():
        if MediasiteAPI._root_folder_id == None:
            url = 'Home'
            json =  MediasiteAPI.get_mediasite_request(url)
            serializer = HomeSerializer(json)
            if serializer.is_valid:
                MediasiteAPI._root_folder_id = serializer.validated_data['RootFolderId']
        return MediasiteAPI._root_folder_id

    @staticmethod
    def get_folder(name, parent_folder_id):
        if parent_folder_id == None:
            parent_folder_id == MediasiteAPI.get_root_folder_id()
        url = 'Folders?$filter=ParentFolderId eq \'{0}\' and Name eq \'{1}\''.format(parent_folder_id, name)
        json = MediasiteAPI.get_mediasite_request(url)
        serializer = FolderSerializer(json)
        if serializer.is_valid():
            return serializer

    @staticmethod
    def create_folder(name, parent_folder_id):
        folder_to_create = dict(
            Name = name,
            ParentFolderId = parent_folder_id
        )
        return MediasiteAPI.post_mediasite_request('Folders', body=folder_to_create)

    # TODO: the default value of the optional ParentFolderId parameter is hard coded to a value
    # known to be the root folder id of the harvard sandbox.  This is not suitable for production
    # and a means to find the root folder id will need to be part of the code solution
    @staticmethod
    def get_or_create_folder(name, parent_folder_id = 'bc609924a0314d2baf5edbc8524f017614'):
        folder = MediasiteAPI.get_folder(name, parent_folder_id)
        if not folder:
            folder = MediasiteAPI.create_folder(name, parent_folder_id)
        return folder

    def get_mediasite_request(url):
        return MediasiteAPI.mediasite_request(url=url, method='GET')

    def post_mediasite_request(url, body):
        return MediasiteAPI.mediasite_request(url=url, method='POST', body=body)

    def mediasite_request(url, method, body):
        url = 'https://dvsdev.mediasite.video.harvard.edu/mediasite/api/v1/' + url
        #url = 'https://sandbox.mediasite.video.harvard.edu/mediasite/api/v1/' + url
        auth = ('Nick_Carmello', 'daft-jaggy-beauty')
        api_key = '4746f072-7faa-4b91-8fdf-3b3aca910c26'
        #api_key = 'e368e3bb-4a6a-48a7-af17-a868300c6d63'
        headers = {'SfIdentTicket': api_key}
        if method == 'POST':
            r = requests.post(url, auth=auth, headers=headers, params=body)
        else:
            r = requests.get(url, auth=auth, headers=headers)
        return r.json()




