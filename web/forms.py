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
        canvas_api = CanvasAPI(user=self.user)
        accounts = canvas_api.get_accounts_for_current_user()
        if accounts:
            for account in accounts:
                try:
                    school = School.objects.get(canvas_id=account.id)
                    # update school name in case it has changed in Canvas
                    school.name = account.name
                    school.save()
                    if self._is_valid_school_account(school):
                        account_choice = (account.id, account.name)
                        account_choices.add(account_choice)
                except ObjectDoesNotExist:
                    # do nothing since we initialized school above
                    pass

        self.fields['accounts'] = forms.ChoiceField(choices=account_choices,
                                                    required=True)

    @staticmethod
    def _is_valid_school_account(school):
        # a school is a valid choice in the form dropdown if it has all the
        # information required to reliably provision a lecture video Canvas
        # integration
        return school.canvas_id and \
               school.mediasite_root_folder and \
               school.consumer_key and \
               school.shared_secret
