from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View

from core.forms import TestRunForm
from core.models import StatusMapping

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after signup
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


class HomePageView(LoginRequiredMixin,View):
    """Dashboard view displaying KPI cards and recent test runs"""
    def get(self, request):
        return render(request, 'pages/home/home.html')

class NewTestView(LoginRequiredMixin,View):
    """New test run creation form view"""
    def get(self, request):
        form = TestRunForm()
        return render(request, 'pages/newtest.html', {'form': form})

    def post(self, request):
        form = TestRunForm(request.POST, request.FILES)
        if form.is_valid():
            test_run = form.save(commit=False)
            test_run.user = request.user
            test_run.status = StatusMapping.PENDING
            test_run.analysis_version = 1
            test_run.save()
            return redirect('core:results', run_id=test_run.pk)
        return render(request, 'pages/newtest.html', {'form': form})



class RunsView(LoginRequiredMixin,View):
    """Test runs history and filtering view"""
    def get(self, request):
        return render(request, 'pages/runs.html')

class ResultsView(LoginRequiredMixin,View):
    """Test results detail view"""
    def get(self, request, run_id):
        context = {'run_id': run_id}
        return render(request, 'pages/results.html', context)

class ReportsView(LoginRequiredMixin,View):
    """Reports and artifacts browser view"""
    def get(self, request):
        return render(request, 'pages/reports.html')

class SettingsView(LoginRequiredMixin,View):
    """Settings and configuration view"""
    def get(self, request):
        return render(request, 'pages/settings.html')
