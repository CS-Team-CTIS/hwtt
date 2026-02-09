from django.shortcuts import render
from django.views import View


# Create your views here.

class HomePageView(View):
    """Dashboard view displaying KPI cards and recent test runs"""
    def get(self, request):
        return render(request, 'pages/home/home.html')


class NewTestView(View):
    """New test run creation form view"""
    def get(self, request):
        return render(request, 'pages/newtest.html')
    def post(self, request):
        print(request.data)
        return render(request, 'pages/newtest.html')




class RunsView(View):
    """Test runs history and filtering view"""
    def get(self, request):
        return render(request, 'pages/runs.html')


class ResultsView(View):
    """Test results detail view"""
    def get(self, request, run_id):
        context = {'run_id': run_id}
        return render(request, 'pages/results.html', context)


class ReportsView(View):
    """Reports and artifacts browser view"""
    def get(self, request):
        return render(request, 'pages/reports.html')


class SettingsView(View):
    """Settings and configuration view"""
    def get(self, request):
        return render(request, 'pages/settings.html')
