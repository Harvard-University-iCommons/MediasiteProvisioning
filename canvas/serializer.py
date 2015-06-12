from rest_framework import  serializers
from .apimodels import Course, Term, Enrollment, User
from .models import Account

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account

    def create(self, validated_data):
        return Account.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.mediasite_root_folder = validated_data.get('mediasite_root_folder', instance.mediasite_root_folder)
        instance.save()
        return instance

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term

# TODO: filter the enrollments so that we only return Teachers and not students
class EnrollmentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Enrollment

class CourseSerializer(serializers.ModelSerializer):
    enrollments = EnrollmentSerializer(many=True, allow_null=True, default=None)
    teaching_users = UserSerializer(many=True, allow_null=True, default=None)
    term = TermSerializer(allow_null=True)

    class Meta:
        model = Course

