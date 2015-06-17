from django.db import models

# Create your models here.
class AccessControl(models.Model):
    RoleId = models.TextField()
    PermissionMask = models.IntegerField()

class Catalog(models.Model):
    Id = models.TextField()
    LinkedFolderId = models.TextField()
    Name = models.TextField()

class Folder(models.Model):
    Id = models.TextField()
    Name = models.TextField()
    Owner = models.TextField()
    Description = models.TextField()
    CreationDate = models.DateField()
    LastModified = models.DateField()
    ParentFolderId = models.TextField()
    Recycled = models.BooleanField()
    Type = models.TextField()
    IsShared = models.BooleanField()
    IsCopyDestination = models.BooleanField()
    IsReviewEditApproveEnabled = models.BooleanField()

class FolderPermission(models.Model):
    Id = models.TextField()
    "TODO: check with Dave whether this is the right way to model this"
    Permissions = models.ManyToManyField(AccessControl)

class ResourcePermission(models.Model):
    Id = models.TextField()
    Owner = models.TextField()
    InheritPermissions = models.BooleanField()
    AccessControlList = models.ManyToManyField(AccessControl)

class Role(models.Model):
    Id = models.TextField()
    Name = models.TextField()
    Description = models.TextField()

class UserProfile(models.Model):
    Id = models.TextField()
    UserName = models.TextField()
    DisplayName = models.TextField()
    Email = models.EmailField()
    Activated = models.BooleanField()
    TimeZone = models.IntegerField()

class Home(models.Model):
    RootFolderId = models.TextField()