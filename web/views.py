from django.shortcuts import render, get_object_or_404
from django.views import generic
from datetime import datetime
from canvas.apimethods import CanvasAPI
from canvas.apimodels import Term
from mediasite.apimethods import MediasiteAPI
from .forms import IndexForm
from .viewmodels import SearchResults
from .models import School


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
                results.school = School.objects.get(canvas_id = account_id)
                # using counters and enumerations to be able to change the result set by reference
                for n, course in enumerate(results.search_results):
                    # find and add terms
                    term = course.term
                    if term is not None:
                        if term not in terms:
                            terms.append(term)
                    else:
                        # TODO: REMOVE THIS
                        course.term = Term(name="Not a term", start_at=datetime.now())

                    # find and add years
                    # TODO: calendar years do not necessarily make sense for this application.  Should be be
                    # looking at academic years, and if so, what are the cutoff dates?
                    if course.start_at is not None:
                        year = course.start_at.year
                        if year not in years:
                            years.append(year)

                    # set the value of the search results to the modified value
                    results.search_results[n] = course

                results.terms = terms
                results.years = years
            else:
                results.count = 0

    else:
        form = IndexForm()

    return render(request, 'web/index.html', {'form' : form, 'results' : results})

def provision(request):
    mediasite_root_folder = request.POST['root_folder']
    course_term = request.POST['term']
    course_id = request.POST['course_id']

    root_folder = MediasiteAPI.get_or_create_folder(name=mediasite_root_folder, parent_folder_id=None)



