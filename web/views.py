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
import logging
from datetime import datetime
from canvas.apimethods import CanvasAPI, CanvasServiceException
from canvas.apimodels import Term, SearchResults
from mediasite.apimethods import MediasiteAPI, MediasiteServiceException
from mediasite.apimodels import UserProfile, Role
from .forms import IndexForm
from .models import School, Log, APIUser

logger = logging.getLogger(__name__)


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
        if ce.status_code() == 401:
            # if we get a 401 it means, probably, that the access token that the user has
            # is invalid, or the user does not have a token.  we should redirect them to canvas to get a token
            canvas_redirect_url = CanvasAPI.get_canvas_oauth_redirect_url(client_id=request.user.id)
            return redirect(canvas_redirect_url)
        else:
            log(username=request.user.username, error=error)

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
        oath_consumer_key = settings.OAUTH_CONSUMER_KEY
        shared_secret = settings.OAUTH_SHARED_SECRET
        catalog_show_date = False
        catalog_show_time = False
        catalog_items_per_page = 100

        if account is not None:
            catalog_show_date = account.catalog_show_date
            catalog_show_time = account.catalog_show_time
            if account.catalog_items_per_page is not None:
                catalog_items_per_page = account.catalog_items_per_page

        if account.consumer_key and account.shared_secret:
            oath_consumer_key = account.consumer_key
            shared_secret = account.shared_secret

        if oath_consumer_key and shared_secret:
            # Initialize an instance of the CanvasAPI with a user, to allow the use of credentials
            # for communication with Canvas
            canvas_api=CanvasAPI(user=request.user)

            # get the course from Canvas.
            course = canvas_api.get_course(course_id)

            if hasattr(course, 'sis_course_id') == False:
                raise Exception('While you can communicate with Canvas, you do not have permissions to view '
                                'SIS properties and will not be able to provision courses.')

            if getattr(course, 'sis_course_id', None) is None:
                raise Exception('The course that you are trying to provision [{0}], does not have an SIS course '
                                'Id and provisioning cannot continue.  Please contact your Canvas '
                                'administrator'.format(course_id))

            # course long name
            course_long_name = "({0}) {1} {2} ({3})"\
                .format(term, course.course_code, course.name, course.sis_course_id)

            logger.info(
                "{} is attempting to provision course with sis id {} and long name {}".format(
                    request.user.username, course.sis_course_id, course_long_name))

            # create the Mediasite folder structure
            course_folder = None
            year_folder = None
            term_folder = None
            root_folder = MediasiteAPI.get_or_create_folder(name=mediasite_root_folder, parent_folder_id=None)
            if root_folder is not None:
                if term.lower()== 'ongoing':
                    # First check for Ongoing terms(The Ongoing term also have
                    # year=None, so do the term check first so it doesn't raise
                    # an Exception in the next block)
                    # For such terms, do not create a folder for the year, move
                    # onto the term folder.(essentially collapsing the folder structure).(TLT-2856)
                    term_folder = MediasiteAPI.get_or_create_folder(name=term, parent_folder_id=root_folder.Id)
                elif year == 'None':
                    #If the year is not set, raise an error
                    raise Exception('Sorry, there was an error provisioning this'
                                    ' course. Please contact video-support@harvard.edu')
                else:
                    year_folder = MediasiteAPI.get_or_create_folder(name=year, parent_folder_id=root_folder.Id)

            if year_folder is not None:
                term_folder = MediasiteAPI.get_or_create_folder(name=term, parent_folder_id=year_folder.Id)

            if term_folder is not None:
                course_folder = MediasiteAPI.get_or_create_folder(name=course_long_name,
                                                                  parent_folder_id=term_folder.Id,
                                                                  alternate_search_term=course.sis_course_id,
                                                                  is_copy_destination=True,
                                                                  is_shared=True)

            if course_folder is not None:
                # create course catalog, with course instance id to ensure uniqueness
                catalog_display_name = '{0}-{1}-{2}-{3}-lecture-video'\
                    .format(mediasite_root_folder, term, course.course_code, course.sis_course_id)
                # this is needed because a bug in Mediasite allows for the creation of a URL with potentially
                # dangerous strings in it. we strip out the characters that we know might create that type of URL
                catalog_display_name = catalog_display_name.translate(None, '<>*%:&\\ ')
                course_catalog = MediasiteAPI.get_or_create_catalog(friendly_name=catalog_display_name,
                                                                    catalog_name=course_long_name,
                                                                    course_folder_id=course_folder.Id,
                                                                    search_term=course.sis_course_id)
                if course_catalog is not None:
                    MediasiteAPI.set_catalog_settings(course_catalog.Id, catalog_show_date, catalog_show_time, catalog_items_per_page)

                    # create Mediasite module if it doesn't exist
                    course_module = MediasiteAPI.get_or_create_module(
                        course.sis_course_id,
                        catalog_display_name,
                        catalog_mediasite_id=course_catalog.Id)

                    # associate the module with the catalog
                    existing_association = next(
                        (a for a in course_module.Associations
                         if course_catalog.Id in a),
                        None)
                    if existing_association is None:
                        MediasiteAPI.add_module_association_by_mediasite_id(
                            course_module.Id, course_catalog.Id)

                ###################################
                # Assign permissions
                ###################################
                # get existing permissions for course folder
                folder_permissions = MediasiteAPI.get_folder_permissions(course_folder.Id)

                # NOTE: The following calls to `update_folder_permissions` do
                # NOT actually call out to the Mediasite API.  Instead, they
                # build up the `folder_permissions` Python list model.  The
                # ultimate call to `assign_permissions_to_folder` makes the
                # API call that passes up the list of permissions to Mediasite.
                # As a future TBD, we should consider taking the
                # `update_folder_permission` method out of the `apimethods`
                # module since it's not actually an API call.

                # create student role if it does not exist, and update (in memory) the permission set for the folder
                directory_entry = "{0}@{1}".format(course.sis_course_id, oath_consumer_key)
                course_role = MediasiteAPI.get_or_create_role(role_name=course_long_name, directory_entry=directory_entry)
                folder_permissions = MediasiteAPI.update_folder_permissions(
                    folder_permissions, course_role, MediasiteAPI.VIEW_ONLY_PERMISSION_FLAG)

                # create Instructor role if it does not exist
                directory_entry = "{0}@{1}".format("urn:lti:role:ims/lis/Instructor:{0}".format(course.sis_course_id), oath_consumer_key)
                course_role = MediasiteAPI.get_or_create_role(role_name="{0} [Instructor]".format(course_long_name), directory_entry=directory_entry)
                folder_permissions = MediasiteAPI.update_folder_permissions(
                    folder_permissions, course_role, MediasiteAPI.READ_WRITE_PERMISSION_FLAG)

                # create Teaching assistant role if it does not exist
                directory_entry = "{0}@{1}".format("urn:lti:role:ims/lis/TeachingAssistant:{0}".format(course.sis_course_id), oath_consumer_key)
                course_role = MediasiteAPI.get_or_create_role(role_name="{0} [Teaching Assistant]".format(course_long_name), directory_entry=directory_entry)
                folder_permissions = MediasiteAPI.update_folder_permissions(
                    folder_permissions, course_role, MediasiteAPI.READ_WRITE_PERMISSION_FLAG)

                # remove permissions for general canvas users users from the in memory permission set
                # so that the course folder is secured
                canvas_user_role = MediasiteAPI.get_role_by_directory_entry('canvas@{0}'.format(oath_consumer_key))
                if canvas_user_role:
                    folder_permissions = MediasiteAPI.update_folder_permissions(
                        folder_permissions, canvas_user_role, MediasiteAPI.NO_ACCESS_PERMISSION_FLAG)

                # remove authenticateduser role
                authenticated_users_role = MediasiteAPI.get_role_by_name('AuthenticatedUsers')
                if authenticated_users_role:
                    folder_permissions = MediasiteAPI.update_folder_permissions(
                        folder_permissions, authenticated_users_role, MediasiteAPI.NO_ACCESS_PERMISSION_FLAG)

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
                    course_term=course.term.name,
                    url=settings.MEDIASITE_LTI_LAUNCH_URL,
                    consumer_key=oath_consumer_key,
                    shared_secret=shared_secret)

                return HttpResponse(content=course_catalog.CatalogUrl)
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
    logger.exception("username %s encountered an error: %s", username, str(error))
