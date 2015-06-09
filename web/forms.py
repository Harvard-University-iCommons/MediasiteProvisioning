from django import forms
from canvas.apimethods import CanvasAPI

class IndexForm(forms.Form):
    account_choices = list()
    for account in CanvasAPI.get_accounts_for_current_user():
        account_choice = ((account['id'], account['name']))
        account_choices.append(account_choice)

    accounts = forms.ChoiceField(choices=account_choices, required=True)
    search = forms.CharField(min_length=3,
                             widget=forms.TextInput(attrs={'placeholder': 'Search term'}))

    search_results = ()

