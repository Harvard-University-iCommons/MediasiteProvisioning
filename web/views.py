from django.shortcuts import render, get_object_or_404
from django.views import generic
from datetime import datetime
from canvas.apimethods import CanvasAPI
from .forms import IndexForm
from .viewmodels import SearchResults


# Create your views here.
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
                # using counters and enumerations to be able to change the result set by reference
                for n, course in enumerate(results.search_results):
                    # update the enrollment data which is not pulled by the search API
                    if False:
                        results.search_results[n]['enrollments'] = \
                            get_enrollments(course_id=course['id'], update_user_email=False)

                    # get the teaching users
                    results.search_results[n]['teaching_users'] = CanvasAPI.get_teaching_users_for_course(course['id'])

                    # find and add terms
                    term = course['term']
                    if term not in terms:
                        terms.append(term)

                    # find and add years
                    if course['start_at'] is not None:
                        year = course['start_at'].year
                        if year not in years:
                            years.append(year)

                results.terms = terms
                results.years = years
            else:
                results.count = 0

    else:
        form = IndexForm()

    return render(request, 'web/index.html', {'form' : form, 'results' : results})

def get_enrollments(course_id, update_user_email):
    enrollments = CanvasAPI.get_enrollments_for_teachers_and_tas(course_id=course_id)
    # find users for enrollments to add the email address, not available in the
    # enrollments API call
    if update_user_email:
        for enrollment_counter, enrollment in enumerate(enrollments):
            enrollments[enrollment_counter]['user'] = CanvasAPI.get_user_profile(enrollment['user']['id'])
    return enrollments
