from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


# @TODO fix template to show errors
class CustomLoginView(LoginView):
    form_class = AuthenticationForm
    extra_context = {
        'page_title': 'Login'
    }
    #success_url = '/'
    template_name = 'login.html'
