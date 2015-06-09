from django.shortcuts import render, get_object_or_404
from django.views import generic
from canvas.apimethods import CanvasAPI
from .forms import IndexForm
from datetime import datetime

# Create your views here.
def search(request):
    search_results = ()
    terms = list()
    years = list()
    if request.method == 'POST':
        form = IndexForm(request.POST)
        if form.is_valid():
            account_id = request.POST['accounts']
            search_term = request.POST['search']
            search_results = CanvasAPI.search_courses(account_id=account_id, search_term=search_term)
            for search_result in search_results:
                term = search_result['term']
                if term not in terms:
                    terms.append(term)
                year = search_result['start_at'].year
                if year not in years:
                    years.append(year)

    else:
        form = IndexForm()

    return render(request, 'web/index.html', {'form' : form, 'search_results' : search_results, 'terms' : terms, 'years' : years})


