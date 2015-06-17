from django import forms
from django.core.exceptions import ObjectDoesNotExist
from canvas.apimethods import CanvasAPI
from .models import School

class IndexForm(forms.Form):
    account_choices = list()
    accounts = CanvasAPI.get_accounts_for_current_user()
    for account in accounts:
        account_choice = ((account.id, account.name))
        account_choices.append(account_choice)
        # we also save/update account information
        # TODO: we may want to look at this for performance
        school = School(canvas_id = account.id, name = account.name)
        try:
            school = School.objects.get(canvas_id = account.id)
            school.name = account.name
        except ObjectDoesNotExist:
            # do nothing since we initialized school above
            pass
        school.save()

    accounts = forms.ChoiceField(choices=account_choices, required=True)
    search = forms.CharField(min_length=3,
                             widget=forms.TextInput(attrs={'placeholder': 'Search term'}))

    search_results = ()

