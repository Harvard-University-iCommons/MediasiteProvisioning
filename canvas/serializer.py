from rest_framework import  serializers
from .apimodels import Course, Term, Enrollment, User, Account, ModuleItem, Module, ExternalTool, Link

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = '__all__'

class ModuleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleItem
        fields = '__all__'

class ModuleSerializer(serializers.ModelSerializer):
    items = ModuleItemSerializer(many=True, allow_null=True, default=None)

    class Meta:
        model = Module
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(allow_null=True, default=None)

    class Meta:
        model = Enrollment
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    enrollments = EnrollmentSerializer(many=True, allow_null=True, default=None)
    teaching_users = UserSerializer(many=True, allow_null=True, default=None)
    term = TermSerializer(allow_null=True, default=None)
    modules = ModuleSerializer(many=True, allow_null=True, default=None)

    class Meta:
        model = Course
        fields = '__all__'

class ExternalToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalTool
        fields = '__all__'

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = '__all__'

