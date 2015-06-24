from rest_framework import  serializers
from .apimodels import Course, Term, Enrollment, User, Account, ModuleItem, Module, ExternalTool

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term

class ModuleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleItem

class ModuleSerializer(serializers.ModelSerializer):
    items = ModuleItemSerializer(many=True, allow_null=True, default=None)

    class Meta:
        model = Module

class EnrollmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(allow_null=True, default=None)

    class Meta:
        model = Enrollment

class CourseSerializer(serializers.ModelSerializer):
    enrollments = EnrollmentSerializer(many=True, allow_null=True, default=None)
    teaching_users = UserSerializer(many=True, allow_null=True, default=None)
    term = TermSerializer(allow_null=True, default=None)
    modules = ModuleSerializer(many=True, allow_null=True, default=None)

    class Meta:
        model = Course

class ExternalToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalTool

