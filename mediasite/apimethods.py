import requests

from .serializer import FolderSerializer, FolderPermissionSerializer

def get_folder(name, parent_folder_id):
    url = 'Folders?$filter=ParentFolderId eq \'{0}\' and Name eq \'{1}\''.format(parent_folder_id, name)
    json = get_mediasite_request(url)
    serializer = FolderSerializer(json)
    if serializer.is_valid():
        return serializer

def get_mediasite_request(url):
    url = 'https://sandbox.mediasite.video.harvard.edu/mediasite/api/v1/' + url
    auth = ('Nick_Carmello', 'daft-jaggy-beauty')
    api_key = 'e368e3bb-4a6a-48a7-af17-a868300c6d63'
    r = requests.get(url, auth=auth, params={"api_key": api_key})
    return r.json()


