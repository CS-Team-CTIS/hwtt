from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# ==============================================================================
# BLUEPRINT: Future Mapping Models for Enum Values
# ==============================================================================
# These models can be implemented later to provide extensible enum mappings
# stored in the database instead of hardcoded choices.
#
# class FileTypeMapping(models.Model):
#     """Mapping for file_type enum values (e.g., CSV, XLSX, JSON)"""
#     code = models.CharField(max_length=50, unique=True)
#     description = models.CharField(max_length=255)
#     is_active = models.BooleanField(default=True)
#
#     def __str__(self):
#         return f"{self.code} - {self.description}"
#
class StatusMapping(models.IntegerChoices):
    """Mapping for test_run status enum values (e.g., PENDING, RUNNING, COMPLETED, FAILED)"""
    PENDING = 1, 'PENDING'
    RUNNING = 2, 'RUNNING'
    COMPLETED = 3, 'COMPLETED'
    FAILED = 4, 'FAILED'

class RatingClassificationMapping(models.IntegerChoices):
    """Mapping for rating_classification enum values (e.g., EXCELLENT, GOOD, FAIR, POOR)"""
    EXCELLENT = 1, 'EXCELLENT'
    GOOD = 2, 'GOOD'
    FAIR = 3, 'FAIR'
    POOR = 4, 'POOR'

# class ArtifactTypeMapping(models.Model):
#     """Mapping for test_artifacts type enum values (e.g., IMAGE, VIDEO, REPORT, LOG)"""
#     code = models.CharField(max_length=50, unique=True)
#     description = models.CharField(max_length=255)
#     is_active = models.BooleanField(default=True)
#
#     def __str__(self):
#         return f"{self.code} - {self.description}"
# ==============================================================================


class TestRun(models.Model):
    """
    Represents a test run session for hardware testing.
    Links to the User who initiated the test.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_runs')
    specimen = models.CharField(max_length=255, help_text="Test specimen identifier")
    binder_grade = models.CharField(max_length=100, help_text="Binder grade specification")
    file_type = models.CharField(max_length=50, help_text="Type of input file (enum placeholder)")
    allowed_rut_depth = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Maximum allowed rut depth in mm"
    )
    notes = models.TextField(null=True, blank=True, help_text="Optional notes about the test run")
    file_path = models.CharField(max_length=500, help_text="Path to the test data file")
    status = models.IntegerField(choices=StatusMapping.choices, help_text="Test run status")
    errors = models.TextField(null=True, blank=True, help_text="Error messages if any")
    analysis_version = models.IntegerField(help_text="Version of the analysis algorithm used")

    # Timestamps
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

    def __str__(self):
        return f"{self.specimen} - {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class TestResults(models.Model):
    """
    Stores aggregated results for a test run.
    One-to-one relationship with TestRun (deleted when TestRun is deleted).
    """
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='results')
    passes_total = models.BigIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Total number of passes in the test"
    )

    # Rut depth measurements at different pass counts
    rut_depth_5000 = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Rut depth at 5000 passes (mm)"
    )
    rut_depth_10000 = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Rut depth at 10000 passes (mm)"
    )
    rut_depth_15000 = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Rut depth at 15000 passes (mm)"
    )
    rut_depth_20000 = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Rut depth at 20000 passes (mm)"
    )
    rut_depth_final = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Final rut depth measurement (mm)"
    )

    passes_to_failure = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Number of passes until failure occurred"
    )
    inflection_pass = models.BigIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Pass number where inflection point occurred"
    )

    test_duration = models.DurationField(help_text="Total duration of the test")
    rating = models.FloatField(help_text="Numerical rating of the test results")
    rating_classification = models.CharField(
        choices=RatingClassificationMapping.choices,
        help_text="Classification of the rating (enum placeholder)"
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
    Individual measurement data points for a test result.
    Multiple measurements per TestResults (deleted when TestResults is deleted).
    """
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='measurements')
    pass_count = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Pass number for this measurement"
    )
    rut_depth_mm = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Measured rut depth in millimeters"
    )
    ref_depth_mm = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0)],
        help_text="Reference depth measurement in millimeters"
    )

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
    Files and artifacts generated during or associated with a test result.
    Multiple artifacts per TestResults (deleted when TestResults is deleted).
    """
    test_results = models.ForeignKey(TestResults, on_delete=models.CASCADE, related_name='artifacts')
    type = models.CharField(
        max_length=50,
        help_text="Type of artifact (enum placeholder: IMAGE, VIDEO, REPORT, LOG, etc.)"
    )
    path = models.CharField(max_length=500, help_text="File path or URL to the artifact")

    class Meta:
        db_table = 'test_artifacts'
        verbose_name_plural = 'Test Artifacts'
        indexes = [
            models.Index(fields=['test_results', 'type']),
        ]

    def __str__(self):
        return f"{self.type} - {self.path}"

