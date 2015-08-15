from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseServerError, HttpResponse
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import string
import sys
import json
from datetime import datetime
from canvas.apimethods import CanvasAPI, CanvasServiceException
from canvas.apimodels import Term, SearchResults
from mediasite.apimethods import MediasiteAPI, MediasiteServiceException
from mediasite.apimodels import UserProfile, Role
from .forms import IndexForm
from .models import School, Log, APIUser

@login_required()
def search(request):
    results = None
    form = None
    error = None
    try:
        if request.method == 'POST':
            form = IndexForm(request.POST, user=request.user)
            if form.is_valid():
                account_id = request.POST['accounts']
                search_term = request.POST['search']
                page = request.POST['page']

                canvas_api = CanvasAPI(user=request.user)

                results = canvas_api.search_courses(account_id=account_id, search_term=search_term, page=page)
                if len(results.search_results) > 0:
                    results.school = School.objects.get(canvas_id=account_id)
                else:
                    results.count = 0
        else:
            form = IndexForm(request.GET, user=request.user)
    except CanvasServiceException as ce:
        canvas_exception = ce._canvas_exception
        error = '{0} [{1}]'.format(ce, canvas_exception)
        log(username=request.user.username, error=error)

        if ce.status_code() == 401:
            # if we get a 401 it means, probably, that the access token that the user has
            # is invalid, or the user does not have a token.  we should redirect them to canvas to get a token
            canvas_redirect_url = CanvasAPI.get_canvas_oauth_redirect_url(client_id=request.user.id)
            return redirect(canvas_redirect_url)

    except Exception as e:
        error = e
        log(username=request.user.username, error=error)

    return render(request, 'web/index.html', {'form': form, 'results': results, 'error': error})

@login_required()
def provision(request):
    try:
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
            course_long_name = "({0}) {1} {2} ({3})"\
                .format(term, course.course_code, course.name, course.sis_course_id)

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
                catalog_display_name = '{0}-{1}-{2}-lecture-video'\
                    .format(mediasite_root_folder, term, course.course_code)
                # this is needed because a bug in Mediasite allows for the creation of a URL with potentially
                # dangerous strings in it. we strip out the characters that we know might create that type of URL
                catalog_display_name = catalog_display_name.translate(dict((ord(char), None) for char in '<>*%:&\\ '))
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
                canvas_user_role = MediasiteAPI.get_role_by_directory_entry('canvas@{0}'.format(oath_consumer_key))
                if canvas_user_role:
                    folder_permissions = MediasiteAPI.update_folder_permissions(
                        folder_permissions, canvas_user_role, MediasiteAPI.NO_ACCESS_PERMISSION_FLAG)

                # iterate through the teachers for this course, find or create their users in Mediasite and
                # add read write permissions to the in memory permission set
                if settings.CREATE_USER_PROFILES_FOR_TEACHERS:
                    # get the teaching users for the course from Canvas
                    canvas_teachers = canvas_api.get_enrollments(course_id=course_id, include_user_email=True)

                    for canvas_teacher in canvas_teachers:
                        teacher_user = MediasiteAPI.get_user_by_email_address(canvas_teacher.user.primary_email)
                        if teacher_user is None:
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

                return HttpResponse(content='Successfully provisioned Mediasite course {0} and connected it to Canvas'
                                    .format(course_long_name))
            else:
                return HttpResponseServerError(content='Unable to create or find Mediasite course folder : {0}'
                                               .format(course_long_name))
        else:
            return HttpResponseServerError(content='The system is not configured to communicate with Mediasite. '
                                                   'School/account : {0}'.format(account.name))
    except CanvasServiceException as ce:
        canvas_exception = ce._canvas_exception
        error = '{0} [{1}]'.format(ce, canvas_exception)
        log(username=request.user.username, error=error)
        return HttpResponseServerError(content='Canvas error : {0}'.format(error))
    except MediasiteServiceException as me:
        mediasite_exception = me._mediasite_exception
        error = '{0} [{1}-{2}]'.format(me, mediasite_exception, me.server_error())
        log(username=request.user.username, error=error)
        return HttpResponseServerError(content='Mediasite error : {0}'.format(error))
    except Exception as e:
        error = e
        log(username=request.user.username, error=error)
        return HttpResponseServerError(content='Unknown error : {0}'.format(error))

@login_required()
def oauth(request):
    try:
        code = request.GET['code']
        state = request.GET['state']

        # make sure that this response is for the logged in user
        if state == str(request.user.id):
            canvas_api = CanvasAPI(user=request.user)
            canvas_api_key = canvas_api.get_canvas_api_key(code=code)
            user = User.objects.get(id=state)
            api_user = None
            try:
                api_user = user.apiuser
            except ObjectDoesNotExist:
                # do nothing
                pass
            if api_user is None:
                api_user = APIUser()
                api_user.user_id = user.id
            api_user.canvas_api_key = canvas_api_key
            api_user.save()

        return redirect('/')
    except Exception as e:
        error = e
        log(username=request.user.username, error=error)

def log(username, error):
    log = Log(username=username, error=error)
    log.save()
