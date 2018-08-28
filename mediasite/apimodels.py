from django.db import models

# Create your models here.

class BaseSerializedModel(models.Model):
    Id = models.TextField(blank=True, null=True)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class AccessControl(BaseSerializedModel):
    RoleId = models.TextField()
    PermissionMask = models.IntegerField()

class Catalog(BaseSerializedModel):
    LinkedFolderId = models.TextField()
    Name = models.TextField()
    FriendlyName = models.TextField(null=True, blank=True)
    CatalogUrl = models.TextField()
    LimitSearchToCatalog = models.BooleanField()

class CatalogSetting(BaseSerializedModel):
    PresentationsPerPage = models.IntegerField()
    ShowCardPresentationDate = models.BooleanField()
    ShowCardPresentationTime = models.BooleanField()
    ShowTablePresentationDate = models.BooleanField()
    ShowTablePresentationTime = models.BooleanField()
    AllowLoginControls = models.BooleanField()

class Folder(BaseSerializedModel):
    Name = models.TextField()
    Owner = models.TextField()
    Description = models.TextField(blank=True, null=True)
    CreationDate = models.DateTimeField()
    LastModified = models.DateTimeField()
    ParentFolderId = models.TextField()
    Recycled = models.BooleanField()
    Type = models.TextField()
    IsShared = models.BooleanField()
    IsCopyDestination = models.BooleanField()
    IsReviewEditApproveEnabled = models.BooleanField()

class FolderPermission(BaseSerializedModel):
    Owner = models.TextField()
    Permissions = list()

class Module(BaseSerializedModel):
    ModuleId = models.TextField()
    Name = models.TextField()
    Associations = list()

class ResourcePermission(BaseSerializedModel):
    Owner = models.TextField()
    InheritPermissions = models.BooleanField()
    AccessControlList = list()

    def __init__(self, **kwargs):
        # ResourcePermissions has a hierarchy which needs to be manually initialized
        self.__dict__.update(kwargs)
        access_control_list = kwargs['AccessControlList']
        if access_control_list:
            self.AccessControlList = [AccessControl(**attrs) for attrs in access_control_list]

class Role(BaseSerializedModel):
    Name = models.TextField()
    Description = models.TextField(null=True, blank=True)
    DirectoryEntry = models.TextField(null=True, blank=True)

class UserProfile(BaseSerializedModel):
    UserName = models.TextField()
    DisplayName = models.TextField()
    Email = models.EmailField()
    Activated = models.BooleanField()
    TimeZone = models.IntegerField()

class Home(BaseSerializedModel):
    RootFolderId = models.TextField()
