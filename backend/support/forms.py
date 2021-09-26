from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from django import forms


class LoginForm(forms.Form):
    login = forms.CharField(max_length=256, min_length=1, label='Логин')


class CreateUserForm(UserCreationForm):
    pass


class FileUploadForm(forms.Form):
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
