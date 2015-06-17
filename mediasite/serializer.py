from rest_framework import  serializers
from .apimodels import Role, Catalog, ResourcePermission, FolderPermission, Folder, Home

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role

class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog

class ResourcePermissionSerializer(serializers.ModelSerializer):
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
