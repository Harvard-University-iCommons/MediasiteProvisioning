from rest_framework import  serializers
from .apimodels import Role, Catalog, ResourcePermission, FolderPermission, Folder, Home, UserProfile, AccessControl

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role

class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog

class AccessControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessControl

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
