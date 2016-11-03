from rest_framework import  serializers
from .apimodels import (
    AccessControl,
    Catalog,
    CatalogSetting,
    Folder,
    FolderPermission,
    Home,
    Module,
    ResourcePermission,
    Role,
    UserProfile, )

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role

class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog

class CatalogSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogSetting

class AccessControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessControl

class ModuleSerializer(serializers.ModelSerializer):
    Associations = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Module

class ResourcePermissionSerializer(serializers.ModelSerializer):
    AccessControlList = AccessControlSerializer(many=True)
    class Meta:
        model = ResourcePermission

class FolderPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderPermission

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder

class HomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Home

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
