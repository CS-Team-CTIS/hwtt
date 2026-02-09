from django.urls import path

from core import views
from django.contrib.auth import views as auth_views

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.HomePageView.as_view(), name='home'),
    path('new-test/', views.NewTestView.as_view(), name='new_test'),
    path('runs/', views.RunsView.as_view(), name='runs'),
    path('runs/<int:run_id>/', views.ResultsView.as_view(), name='results'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('settings/', views.SettingsView.as_view(), name='settings'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Or custom views
    path('signup/', views.signup, name='signup'),
]
