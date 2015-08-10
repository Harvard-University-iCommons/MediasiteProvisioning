from django import forms
from django.core.exceptions import ObjectDoesNotExist
from canvas.apimethods import CanvasAPI
from .models import School

class IndexForm(forms.Form):
    accounts = None
    search = forms.CharField(min_length=3, widget=forms.TextInput(attrs={'placeholder': 'Please enter at least 3 characters'}))
    search_results = ()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(IndexForm, self).__init__(*args, **kwargs)

        account_choices = list()
        canvas_api = CanvasAPI(user=self.user)
        accounts = canvas_api.get_accounts_for_current_user()
        if accounts:
            for account in accounts:
                account_choice = ((account.id, account.name))
                account_choices.append(account_choice)
                # we also save/update account information
                school = School(canvas_id=account.id, name=account.name)
                try:
                    school = School.objects.get(canvas_id = account.id)
                    school.name = account.name
                except ObjectDoesNotExist:
                    # do nothing since we initialized school above
                    pass
                school.save()

        self.fields['accounts'] = forms.ChoiceField(choices=account_choices, required=True)





