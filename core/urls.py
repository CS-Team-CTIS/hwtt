from django.urls import path

from core import views
from django.contrib.auth import views as auth_views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('home/', views.HomePageView.as_view(), name='home'),
    path('new-test/', views.NewTestView.as_view(), name='new_test'),
    path('runs/', views.RunsView.as_view(), name='runs'),
    path('runs/<int:run_id>/', views.ResultsView.as_view(), name='results'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('settings/', views.SettingsView.as_view(), name='settings'),

    path('validate-file/',views.ValidateFile.as_view(),name='validate-file'),
    path('binder-grade-max-rut/', views.BinderGradeMaxRutView.as_view(), name='binder_grade_max_rut'),
    path('settings/binder-grades/new/', views.BinderGradeCreateView.as_view(), name='binder_grade_create'),
    path('settings/binder-grades/<int:pk>/edit/', views.BinderGradeEditView.as_view(), name='binder_grade_edit'),

    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Or custom views
    path('signup/', views.signup, name='signup'),
]
