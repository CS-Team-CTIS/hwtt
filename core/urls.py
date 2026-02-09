from django.urls import path

from core import views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.HomePageView.as_view(), name='home'),
    path('new-test/', views.NewTestView.as_view(), name='new_test'),
    path('runs/', views.RunsView.as_view(), name='runs'),
    path('runs/<int:run_id>/', views.ResultsView.as_view(), name='results'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
