from django import forms

from .models import School
from canvas.apimethods import CanvasAPI


class IndexForm(forms.Form):
    accounts = None
    search = forms.CharField(min_length=3, widget=forms.TextInput(
        attrs={'placeholder': 'Please enter at least 3 characters'}))
    search_results = ()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(IndexForm, self).__init__(*args, **kwargs)

        schools = School.objects.order_by('name').values_list(
            'canvas_id', 'name')

        if not self.user.is_staff:
            canvas_api = CanvasAPI(user=self.user)
            accounts = canvas_api.get_accounts_for_current_user()
            account_ids = set([a.id for a in accounts])
            schools = schools.filter(canvas_id__in=account_ids)

        self.fields['accounts'] = forms.ChoiceField(schools, required=True)
