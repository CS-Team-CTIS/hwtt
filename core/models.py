import os

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class TestRunStatus(models.IntegerChoices):
    PENDING = 1, 'PENDING'
    RUNNING = 2, 'RUNNING'
    COMPLETED = 3, 'COMPLETED'
    FAILED = 4, 'FAILED'


class RatingClassification(models.IntegerChoices):
    EXCELLENT = 1, 'EXCELLENT'
    GOOD = 2, 'GOOD'
    FAIR = 3, 'FAIR'
    POOR = 4, 'POOR'


class TestFileType(models.IntegerChoices):
    INSTROTEK = 1, 'INSTROTEK'
    TROXLER = 2, 'TROXLER'
    PTI = 3, 'PTI'
    CUSTOM = 4, 'CUSTOM'


def validate_file(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.csv', '.xlsx', '.txt']
    if ext.lower() not in valid_extensions:
        raise ValidationError('Only .csv,.xlsx,.txt files are allowed.')


class BinderGrade(models.Model):
    name = models.CharField(max_length=50, unique=True)
    max_rut = models.FloatField(null=True, blank=True, help_text="Default maximum rut depth (mm)")
    passes_to_rut = models.PositiveIntegerField(null=True, blank=True, help_text="Default number of passes to rut failure")

    def __str__(self):
        return self.name


class TestRun(models.Model):
    """
    Represents a test run session for hardware testing.
    Links to the User who initiated the test.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_runs')
    specimen = models.CharField(max_length=255, help_text="Test specimen identifier")
    binder_grade = models.ForeignKey(BinderGrade, on_delete=models.PROTECT)
    file_type = models.IntegerField(choices=TestFileType.choices, help_text="Type of input file")
    allowed_rut_depth = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Maximum allowed rut depth in mm"
    )
    notes = models.TextField(null=True, blank=True, help_text="Optional notes about the test run")
    file = models.FileField(help_text="Data file", upload_to='uploads/%Y/%m/%d/', validators=[validate_file])
    status = models.IntegerField(choices=TestRunStatus.choices, help_text="Test run status")
    errors = models.TextField(null=True, blank=True, help_text="Error messages if any")
    analysis_version = models.IntegerField(help_text="Version of the analysis algorithm used")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'test_run'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]

    @property
    def filename(self):
        from pathlib import Path
        return Path(self.file.name).name

    def __str__(self):
        return f"{self.specimen} - {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def result(self):
        """Safe accessor for the related TestResults (returns None if not yet created)."""
        try:
            return self.results
        except TestResults.DoesNotExist:
            return None


class TestResults(models.Model):
    """
    Stores aggregated results for a test run. One result per run.
    """
    test_run = models.OneToOneField(TestRun, on_delete=models.CASCADE, related_name='results')

    passes_vs_rut = models.TextField()

    passes_vs_rut_denoise = models.TextField()

    passes_total = models.BigIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Total number of passes in the test",
        null=True
    )

    rut_depth_5000 = models.FloatField(validators=[MinValueValidator(0.0)], help_text="Rut depth at 5000 passes (mm)", null=True)
    rut_depth_10000 = models.FloatField(validators=[MinValueValidator(0.0)], help_text="Rut depth at 10000 passes (mm)", null=True)
    rut_depth_15000 = models.FloatField(validators=[MinValueValidator(0.0)], help_text="Rut depth at 15000 passes (mm)", null=True)
    rut_depth_20000 = models.FloatField(validators=[MinValueValidator(0.0)], help_text="Rut depth at 20000 passes (mm)", null=True)
    rut_depth_final = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)], help_text="Final rut depth measurement (mm)")

    passes_to_failure = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)], help_text="Number of passes until failure occurred")
    inflection_pass = models.BigIntegerField(null=True, blank=True, validators=[MinValueValidator(0)], help_text="Pass number where inflection point occurred")


    test_duration = models.DurationField(help_text="Total duration of the test", null=True)
    rating = models.FloatField(help_text="Numerical rating of the test results", null=True)
    rating_classification = models.IntegerField(
        choices=RatingClassification.choices,
        help_text="Classification of the rating",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'test_results'
        verbose_name_plural = 'Test Results'
        indexes = [
            models.Index(fields=['test_run']),
            models.Index(fields=['rating_classification']),
        ]



    def __str__(self):
        return f"Results for {self.test_run.specimen} - Rating: {self.rating}"


class TestMeasurements(models.Model):
    """
    Individual measurement data points for a test run.
    """
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='measurements')
    pass_count = models.IntegerField(validators=[MinValueValidator(0)], help_text="Pass number for this measurement")
    rut_depth_mm = models.FloatField(validators=[MinValueValidator(0.0)], help_text="Measured rut depth in millimeters")
    ref_depth_mm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)], help_text="Reference depth measurement in millimeters")

    class Meta:
        db_table = 'test_measurements'
        verbose_name_plural = 'Test Measurements'
        ordering = ['pass_count']
        indexes = [
            models.Index(fields=['test_run', 'pass_count']),
        ]

    def __str__(self):
        return f"Pass {self.pass_count}: {self.rut_depth_mm}mm"


class TestArtifacts(models.Model):
    """
    Files and artifacts associated with a test result.
    """
    test_results = models.ForeignKey(TestResults, on_delete=models.CASCADE, related_name='artifacts')
    type = models.CharField(max_length=50, help_text="Type of artifact (IMAGE, VIDEO, REPORT, LOG, etc.)")
    path = models.CharField(max_length=500, help_text="File path or URL to the artifact")

    class Meta:
        db_table = 'test_artifacts'
        verbose_name_plural = 'Test Artifacts'
        indexes = [
            models.Index(fields=['test_results', 'type']),
        ]

    def __str__(self):
        return f"{self.type} - {self.path}"
