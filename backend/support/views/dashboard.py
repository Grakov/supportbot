from django.contrib.auth import get_user
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse


class DashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        staff_user = get_user(request)
        context = {
            'page_title': 'Главная',
            "staff_user": staff_user
        }
        return render(request, 'dashboard.html', context=context)
