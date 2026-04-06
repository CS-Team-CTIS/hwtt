from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View

from core.forms import TestRunForm
from core.models import TestRunStatus, TestRun, TestResults, BinderGrade
from core.services import ValidateFileService, AnalysisRunService


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('core:home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


class HomePageView(LoginRequiredMixin, View):
    """Dashboard view displaying KPI cards and recent test runs"""
    def get(self, request):
        runs = TestRun.objects.order_by('created_at')
        return render(request, 'pages/home/home.html', {
            'recent_runs': runs[:10],
            'total_runs': runs.count(),
        })


class NewTestView(LoginRequiredMixin, View):
    """New test run creation form view"""
    def get(self, request):
        return render(request, 'pages/newtest.html', {'form': TestRunForm()})

    def post(self, request):
        form = TestRunForm(request.POST, request.FILES)
        if form.is_valid():

            test_run = form.save(commit=False)
            test_run.user = request.user
            test_run.status = TestRunStatus.PENDING
            test_run.analysis_version = settings.ANALYSIS_VERSION
            test_run.save()

            # TODO: ADD TO TASK QUEUE USING CELERY - For now we will force analysis
            AnalysisRunService.simple_analysis(test_run.file.path, test_run.id)

            return redirect('core:results', run_id=test_run.pk)
        return render(request, 'pages/newtest.html', {'form': form})


class ValidateFile(LoginRequiredMixin, View):
    def post(self, request):
        if 'file' not in request.FILES:
            return redirect('core:new_test')
        validated_file = ValidateFileService.validate_csv(request.FILES['file'])
        return render(request, 'partials/file_preview.html', {
            'rows': validated_file['rows'],
            'cols': validated_file['cols'],
            'is_valid': validated_file['valid'],
            'headers': validated_file['headers'],
        })


class RunsView(LoginRequiredMixin, View):
    """Test runs history and filtering view"""
    def get(self, request):
        qs = TestRun.objects.select_related('binder_grade', 'results')

        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        binder_grade = request.GET.get('binder_grade', '')
        file_type = request.GET.get('file_type', '')
        status = request.GET.get('status', '')
        classification = request.GET.get('classification', '')

        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if binder_grade:
            qs = qs.filter(binder_grade_id=binder_grade)
        if file_type:
            qs = qs.filter(file_type=file_type)
        if status:
            qs = qs.filter(status=status)
        if classification:
            qs = qs.filter(results__rating_classification=classification)

        context = {
            'runs': qs,
            'binder_grades': BinderGrade.objects.all(),
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'binder_grade': binder_grade,
                'file_type': file_type,
                'status': status,
                'classification': classification,
            },
        }

        if request.GET.get('partial') == 'table':
            return render(request, 'partials/runs_table.html', context)
        return render(request, 'pages/runs.html', context)


class ResultsView(LoginRequiredMixin, View):
    """Test results detail view"""
    def get(self, request, run_id):
        test_run = TestRun.objects.select_related('results').get(pk=run_id)
        test_results = test_run.results
        return render(request, 'pages/results.html', {
            'run_id': run_id,
            'passes_vs_rut': test_results.passes_vs_rut,
            'passes_vs_rut_denoise': test_results.passes_vs_rut_denoise,
            'test_run': test_run,
            'test_results': test_results,
        })


class ReportsView(LoginRequiredMixin, View):
    """Reports and artifacts browser view"""
    def get(self, request):
        return render(request, 'pages/reports.html')


class SettingsView(LoginRequiredMixin, View):
    """Settings and configuration view"""
    def get(self, request):
        return render(request, 'pages/settings.html', {'binder_grades': BinderGrade.objects.all()})


def _binder_grades_response(request):
    return render(request, 'partials/binder_grades_rows.html', {
        'binder_grades': BinderGrade.objects.all(),
    })


class BinderGradeMaxRutView(LoginRequiredMixin, View):
    def get(self, request):
        grade_id = request.GET.get('binder_grade')
        max_rut = ''
        if grade_id:
            try:
                max_rut = BinderGrade.objects.get(pk=grade_id).max_rut
            except BinderGrade.DoesNotExist:
                pass
        return render(request, 'partials/max_rut_input.html', {'max_rut': max_rut})


class BinderGradeCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'partials/binder_grade_form.html', {'grade': None})

    def post(self, request):
        name = request.POST.get('name', '').strip()
        max_rut = request.POST.get('max_rut') or None
        passes_to_rut = request.POST.get('passes_to_rut') or None
        if name:
            BinderGrade.objects.get_or_create(name=name, defaults={'max_rut': max_rut, 'passes_to_rut': passes_to_rut})
        return _binder_grades_response(request)


class BinderGradeEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        return render(request, 'partials/binder_grade_form.html', {
            'grade': BinderGrade.objects.get(pk=pk),
        })

    def post(self, request, pk):
        name = request.POST.get('name', '').strip()
        max_rut = request.POST.get('max_rut') or None
        passes_to_rut = request.POST.get('passes_to_rut') or None
        if name:
            BinderGrade.objects.filter(pk=pk).update(name=name, max_rut=max_rut, passes_to_rut=passes_to_rut)
        return _binder_grades_response(request)
