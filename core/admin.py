from django.contrib import admin
from .models import TestRun, TestResults, TestMeasurements, TestArtifacts


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('specimen', 'user', 'binder_grade', 'status', 'file_type', 'created_at')
    list_filter = ('status', 'file_type', 'created_at', 'user')
    search_fields = ('specimen', 'binder_grade', 'user__username', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Test Information', {
            'fields': ('user', 'specimen', 'binder_grade')
        }),
        ('File & Configuration', {
            'fields': ('file_type', 'file_path', 'allowed_rut_depth', 'analysis_version')
        }),
        ('Status & Results', {
            'fields': ('status', 'errors', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TestResults)
class TestResultsAdmin(admin.ModelAdmin):
    list_display = ('test_run', 'passes_total', 'rating', 'rating_classification', 'test_duration')
    list_filter = ('rating_classification',)
    search_fields = ('test_run__specimen', 'test_run__user__username')
    readonly_fields = ('test_run',)
    fieldsets = (
        ('Test Reference', {
            'fields': ('test_run',)
        }),
        ('Pass Information', {
            'fields': ('passes_total', 'passes_to_failure', 'inflection_pass', 'test_duration')
        }),
        ('Rut Depth Measurements', {
            'fields': ('rut_depth_5000', 'rut_depth_10000', 'rut_depth_15000', 'rut_depth_20000', 'rut_depth_final')
        }),
        ('Rating', {
            'fields': ('rating', 'rating_classification')
        }),
    )


@admin.register(TestMeasurements)
class TestMeasurementsAdmin(admin.ModelAdmin):
    list_display = ('test_run', 'pass_count', 'rut_depth_mm', 'ref_depth_mm')
    list_filter = ('test_run',)
    search_fields = ('test_run__specimen',)
    ordering = ('test_run', 'pass_count')


@admin.register(TestArtifacts)
class TestArtifactsAdmin(admin.ModelAdmin):
    list_display = ('test_results', 'type', 'path')
    list_filter = ('type',)
    search_fields = ('test_results__test_run__specimen', 'path')
