from django import forms
from django.forms.widgets import PasswordInput
from ajax_select.fields import AutoCompleteField
from django.utils import timezone

from recommender_webapp.common.utils import ChoiceEnum
from recommender_webapp.models import User, Profile, Comune, Companionship, Mood


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('location',)

    location = AutoCompleteField('cities')

    def clean(self, *args, **kwargs):
        location = self.cleaned_data.get('location')
        location_found = Comune.objects.filter(nome__iexact=location)
        if not location_found.exists():
            raise forms.ValidationError("Location not found")


class UserRegisterForm(forms.ModelForm):
    email = forms.EmailField(label='Email address')
    email2 = forms.EmailField(label='Confirm Email')
    password = forms.CharField(widget=PasswordInput)
    password2 = forms.CharField(widget=PasswordInput, label='Confirm Password')

    class Meta:
        model = User
        fields = [
            'email',
            'email2',
            'password',
            'password2',
            'first_name',
            'last_name'
        ]

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')
        email2 = self.cleaned_data.get('email2')
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if email != email2:
            raise forms.ValidationError("Emails must match")
        if password != password2:
            raise forms.ValidationError("Passwords must match")

        email_qs = User.objects.filter(email=email)
        if email_qs.exists():
            raise forms.ValidationError("This email has already been registered")

        return super(UserRegisterForm, self).clean(*args, **kwargs)


class SearchRecommendationDistanceRange(ChoiceEnum):
    __order__ = 'unlimited km20 km40 km60'
    unlimited = 0
    km20 = 20
    km40 = 40
    km60 = 60


# This form is used for searching recommendations
class SearchRecommendationForm(forms.Form):
    mood = forms.ChoiceField(
        required=True,
        widget=forms.Select,
        choices=[choice[::-1] for choice in Mood.choices()]
    )
    companionship = forms.ChoiceField(
        required=True,
        widget=forms.Select,
        choices=[choice[::-1] for choice in Companionship.choices()]
    )
    km_range = forms.ChoiceField(
        required=False,
        widget=forms.Select,
        choices=[choice[::-1] for choice in SearchRecommendationDistanceRange.choices()],
        label='Distance'
    )
    any_events = forms.BooleanField(initial=False, required=False, label='Any events')


# This form is used for adding a new rating
class AddRatingForm(forms.Form):
    mood = forms.ChoiceField(
        required=True,
        widget=forms.Select,
        choices=[choice[::-1] for choice in Mood.choices()]
    )
    companionship = forms.ChoiceField(
        required=True,
        widget=forms.Select,
        choices=[choice[::-1] for choice in Companionship.choices()]
    )


class SearchPlacesDistanceRange(ChoiceEnum):
    __order__ = 'km5 km10'
    km5 = 5
    km10 = 10
    # km30 = 30
    # km40 = 40
    # km50 = 50


class SearchNearPlacesForm(forms.Form):
    km_range = forms.ChoiceField(
        required=True,
        widget=forms.Select,
        choices=[choice[::-1] for choice in SearchPlacesDistanceRange.choices()]
    )


def past_years(ago):
    this_year = timezone.now().year
    return list(range(this_year - ago - 1, this_year))


class FullProfileForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.SelectDateWidget(years=past_years(100)))

    class Meta:
        model = Profile
        fields = ('location', 'profession', 'birth_date', 'bio')
        # widgets={'birth_date': forms.DateInput(attrs={'class': 'datepicker'})}    # Another type of datepicker

    location = AutoCompleteField('cities')

    def clean(self, *args, **kwargs):
        location = self.cleaned_data.get('location')
        location_found = Comune.objects.filter(nome__iexact=location)
        if not location_found.exists():
            raise forms.ValidationError("Location not found")
