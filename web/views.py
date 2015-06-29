from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from datetime import datetime
from canvas.apimethods import CanvasAPI
from canvas.apimodels import Term
from mediasite.apimethods import MediasiteAPI
from mediasite.apimodels import UserProfile, Role
from .forms import IndexForm
from .viewmodels import SearchResults
from .models import School


@login_required()
def search(request):
    results = SearchResults()
    terms = list()
    years = list()
    if request.method == 'POST':
        form = IndexForm(request.POST, user=request.user)
        if form.is_valid():
            account_id = request.POST['accounts']
            search_term = request.POST['search']

            canvas_api = CanvasAPI(user=request.user)

            results.search_results = canvas_api.search_courses(account_id=account_id, search_term=search_term)
            if len(results.search_results) > 0:
                results.school = School.objects.get(canvas_id=account_id)

                # using counters and enumerations to be able to change the result set by reference
                for n, course in enumerate(results.search_results):
                    # find and add years
                    course.year = None
                    if course.term is not None:
                        course.year = CanvasAPI.get_year_from_term(course.term)
                    if course.year is None and course.start_at is not None:
                        course.year = CanvasAPI.get_year_from_start_date(course.start_at)

                    if course.year not in years:
                        years.append(course.year)

                    # find and add terms
                    if course.term is None:
                        course.term = Term(name='Full Year {0}'.format(course.year), start_at=course.start_at)
                    if next((t for t in terms if t.name == course.term.name), None) is None:
                        terms.append(course.term)

                    # set the value of the search results to the modified value
                    results.search_results[n] = course

                results.terms = terms
                results.years = years
            else:
                results.count = 0

    else:
        form = IndexForm(request.GET, user=request.user)

    return render(request, 'web/index.html', {'form': form, 'results': results})

@login_required()
def provision(request):
    mediasite_root_folder = request.POST['root_folder']
    year = request.POST['year']
    term = request.POST['term']
    course_id = request.POST['course_id']
    account_id = request.POST['account_id']

    account = School.objects.get(canvas_id=account_id)
    oath_consumer_key = None
    shared_secret = None
    if account.consumer_key is not None and account.shared_secret is not None:
        oath_consumer_key = account.consumer_key
        shared_secret = account.shared_secret
    else:
        oath_consumer_key = settings.OAUTH_CONSUMER_KEY
        shared_secret = settings.OAUTH_SHARED_SECRET

    if oath_consumer_key is not None and shared_secret is not None:
        # Initialize an instance of the CanvasAPI with a user, to allow the use of credentials
        # for communication with Canvas
        canvas_api=CanvasAPI(user=request.user)

        # get the course from Canvas.
        course = canvas_api.get_course(course_id)

        # course long name
        course_long_name = "({0}) {1} {2} ({3})".format(term, course.course_code, course.name, course.sis_course_id)
        catalog_display_name = '{0}-{1}-{2}-lecture-video'.format(mediasite_root_folder, term, course.course_code)

        # create the Mediasite folder structure
        course_folder = None
        root_folder = MediasiteAPI.get_or_create_folder(name=mediasite_root_folder, parent_folder_id=None)
        if root_folder is not None:
            year_folder = MediasiteAPI.get_or_create_folder(name=year, parent_folder_id=root_folder.Id)
            if year_folder is not None:
                term_folder = MediasiteAPI.get_or_create_folder(name=term, parent_folder_id=year_folder.Id)
                if term_folder is not None:
                    course_folder = MediasiteAPI.get_or_create_folder(name=course_long_name,
                                                                      parent_folder_id=term_folder.Id)

        if course_folder is not None:
            # create course catalog
            course_catalog = MediasiteAPI.get_or_create_catalog(friendly_name=catalog_display_name,
                                                                catalog_name=course_long_name,
                                                                course_folder_id=course_folder.Id)

            ###################################
            # Assign permissions
            ###################################
            # get existing permissions for course folder
            folder_permissions = MediasiteAPI.get_folder_permissions(course_folder.Id)

            # create student role if it does not exist, and update (in memory) the permission set for the folder
            directory_entry = "{0}@{1}".format(course.sis_course_id, oath_consumer_key)
            course_role = MediasiteAPI.get_or_create_role(role_name=course_long_name, directory_entry=directory_entry)
            folder_permissions = MediasiteAPI.update_folder_permissions(
                folder_permissions, course_role, MediasiteAPI.READ_ONLY_PERMISSION_FLAG)

            # remove permissions for general canvas users users from the in memory permission set
            # so that the course folder is secured
            canvas_user_role_de = 'canvas@{0}'.format(oath_consumer_key)
            authenticated_user_role = MediasiteAPI.get_role_by_directory_entry(canvas_user_role_de)
            if authenticated_user_role:
                folder_permissions = MediasiteAPI.update_folder_permissions(
                    folder_permissions, authenticated_user_role, MediasiteAPI.NO_ACCESS_PERMISSION_FLAG)

            # iterate through the teachers for this course, find or create their users in Mediasite and
            # add read write permissions to the in memory permission set
            if settings.CREATE_USER_PROFILES_FOR_TEACHERS:
                # get the teaching users for the course from Canvas
                canvas_teachers = canvas_api.get_enrollments(course_id=course_id, include_user_email=True)

                for canvas_teacher in canvas_teachers:
                    teacher_user = MediasiteAPI.get_user_by_email_address(canvas_teacher.user.primary_email)
                    if teacher_user is None:
                        # TODO: very low : look into creating an appropriate TimeZone for the user
                        teacher_user = MediasiteAPI.create_user(
                            UserProfile(UserName=canvas_teacher.user.primary_email,
                                        DisplayName=canvas_teacher.user.name,
                                        Email=canvas_teacher.user.primary_email,
                                        Activated=True)
                        )

                    teacher_role = Role(Id = MediasiteAPI.convert_user_profile_to_role_id(teacher_user.Id))

                    folder_permissions = MediasiteAPI.update_folder_permissions(
                        folder_permissions, teacher_role,  MediasiteAPI.READ_WRITE_PERMISSION_FLAG)

            # assign in memory  permissions to folder in Mediasite
            MediasiteAPI.assign_permissions_to_folder(course_folder.Id, folder_permissions)

            # reach back into Canvas and create a module and module items if they do not exist
            canvas_mediasite_module_item = canvas_api.create_mediasite_app_external_link(
                course_id=course.id,
                url=course_catalog.CatalogUrl,
                consumer_key=oath_consumer_key,
                shared_secret=shared_secret)
