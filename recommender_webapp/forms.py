from django import forms
from django.forms.widgets import PasswordInput
from ajax_select.fields import AutoCompleteField

from recommender_webapp.models import User, Profile, Comune


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