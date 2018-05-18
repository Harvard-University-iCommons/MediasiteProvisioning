from rest_framework import serializers
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
        fields = '__all__'

class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog
        fields = '__all__'

class CatalogSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogSetting
        fields = '__all__'

class AccessControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessControl
        fields = '__all__'

class ModuleSerializer(serializers.ModelSerializer):
    Associations = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Module
        fields = '__all__'

class ResourcePermissionSerializer(serializers.ModelSerializer):
    AccessControlList = AccessControlSerializer(many=True)
    class Meta:
        model = ResourcePermission
        fields = '__all__'

class FolderPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderPermission
        fields = '__all__'

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = '__all__'

class HomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Home
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
