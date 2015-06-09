from rest_framework import  serializers
from .apimodels import Course, Account, Term, Enrollment

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term

# TODO: filter the enrollments so that we only return Teachers and not students
class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment

class CourseSerializer(serializers.ModelSerializer):
    #enrollments = EnrollmentSerializer(many=True, allow_null=True)
    term = TermSerializer(allow_null=True)

    class Meta:
        model = Course

    def create(self, validated_data):
        course = Course(
            name = validated_data['name']
        )
        return course
