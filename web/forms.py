from django import forms
from django.core.exceptions import ObjectDoesNotExist

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

        account_choices = set()
        if self.user.is_staff:
            # user should be able to provision for any school
            schools = School.objects.all()
            valid_schools = [(s.canvas_id, s.name) for s in schools
                             if s.can_be_provisioned]
            account_choices = set(valid_schools)
        else:
            canvas_api = CanvasAPI(user=self.user)
            accounts = canvas_api.get_accounts_for_current_user()
            for account in accounts:
                try:
                    school = School.objects.get(canvas_id=account.id)
                    # update school name in case it has changed in Canvas
                    school.name = account.name
                    school.save()
                    if school.can_be_provisioned:
                        account_choice = (account.id, account.name)
                        account_choices.add(account_choice)
                except ObjectDoesNotExist:
                    # do nothing since we initialized school above
                    pass

        sorted_choices = sorted(account_choices, key=lambda a: a[1])
        self.fields['accounts'] = forms.ChoiceField(choices=sorted_choices,
                                                    required=True)
