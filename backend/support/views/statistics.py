from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin


class StatisticsView(LoginRequiredMixin, View):
    pass
