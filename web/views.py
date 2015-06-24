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
        form = IndexForm(request.POST)
        if form.is_valid():
            account_id = request.POST['accounts']
            search_term = request.POST['search']
            results.search_results = CanvasAPI.search_courses(account_id=account_id, search_term=search_term)
            if len(results.search_results) > 0:
                results.school = School.objects.get(canvas_id=account_id)
                # using counters and enumerations to be able to change the result set by reference
                for n, course in enumerate(results.search_results):
                    # find and add years
                    # TODO: calendar years do not necessarily make sense for this application.  Should be be
                    # looking at academic years, and if so, what are the cutoff dates?
                    year = None
                    if course.start_at is not None:
                        year = CanvasAPI.get_year_from_start_date(course.start_at)
                        if year not in years:
                            years.append(year)

                    # find and add terms
                    if course.term is None:
                        course.term = Term(name='Full Year {0}'.format(year), start_at=course.start_at)
                    if course.term not in terms:
                        terms.append(course.term)

                    # set the value of the search results to the modified value
                    results.search_results[n] = course

                results.terms = terms
                results.years = years
            else:
                results.count = 0

    else:
        form = IndexForm()

    return render(request, 'web/index.html', {'form' : form, 'results' : results})

@login_required()
def provision(request):
    mediasite_root_folder = request.POST['root_folder']
    # TODO: pull the actual year
    year = '2014-2015'
    term = request.POST['term']
    course_id = request.POST['course_id']

    # We get the mediasite app from the course.  If there is no app there is no point in proceeding
    external_tool = CanvasAPI.get_mediasite_app_external_tool(course_id)
    if external_tool is not None:
        oath_consumer_key = external_tool.consumer_key

        # get the course from Canvas.
        # TODO: This may not be necessary since we could pass in all the course attributes, but this is more reliable
        # and extensible
        course = CanvasAPI.get_course(course_id)

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

            course_catalog = MediasiteAPI.get_or_create_catalog(catalog_name=course_long_name,
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
            canvas_user_role_de = 'canvas@{0}'.format(external_tool.consumer_key)
            authenticated_user_role = MediasiteAPI.get_role_by_directory_entry(canvas_user_role_de)
            folder_permissions = MediasiteAPI.update_folder_permissions(
                folder_permissions, authenticated_user_role, MediasiteAPI.NO_ACCESS_PERMISSION_FLAG)

            # get the teaching users for the course from Canvas
            canvas_teachers = CanvasAPI.get_enrollments(course_id=course_id, include_user_email=True)

            # iterate through the teachers for this course, find or create their users in Mediasite and
            # add read write permissions to the in memory permission set
            for canvas_teacher in canvas_teachers:
                teacher_user = MediasiteAPI.get_user_by_email_address(canvas_teacher.user.primary_email)
                if teacher_user is None:
                    # TODO: look into creating an appropriate TimeZone for the user
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
            canvas_mediasite_module_item = CanvasAPI.get_or_create_mediasite_module_item(
                course.id,
                course_catalog.CatalogUrl,
                external_tool.id)






