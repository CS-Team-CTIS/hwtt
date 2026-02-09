#!/usr/bin/env python
"""
Test script to verify URL routing and views are properly configured
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hwtt.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from core import views

def test_urls():
    """Test that all URL patterns are correctly configured"""
    print("=" * 60)
    print("Testing URL Configuration")
    print("=" * 60)

    urls_to_test = [
        ('core:home', '/', views.HomePageView),
        ('core:new_test', '/new-test/', views.NewTestView),
        ('core:runs', '/runs/', views.RunsView),
        ('core:results', '/runs/123/', views.ResultsView),
        ('core:reports', '/reports/', views.ReportsView),
        ('core:settings', '/settings/', views.SettingsView),
    ]

    all_passed = True

    for name, expected_path, expected_view in urls_to_test:
        try:
            # Test reverse URL resolution
            if name == 'core:results':
                url = reverse(name, kwargs={'run_id': 123})
            else:
                url = reverse(name)

            if url == expected_path:
                print(f"✅ {name:20} → {url:20} [PASS]")
            else:
                print(f"❌ {name:20} → {url:20} [FAIL] Expected: {expected_path}")
                all_passed = False

            # Test URL resolution to view
            resolved = resolve(url)
            if resolved.func.view_class == expected_view:
                print(f"   View: {expected_view.__name__} [PASS]")
            else:
                print(f"   View: {resolved.func.view_class.__name__} [FAIL] Expected: {expected_view.__name__}")
                all_passed = False

        except Exception as e:
            print(f"❌ {name:20} → ERROR: {e}")
            all_passed = False

        print()

    print("=" * 60)
    if all_passed:
        print("✅ All URL tests passed!")
    else:
        print("❌ Some URL tests failed")
    print("=" * 60)

    return all_passed

def test_views():
    """Test that all views render correctly"""
    print("\n" + "=" * 60)
    print("Testing View Rendering")
    print("=" * 60)

    factory = RequestFactory()
    all_passed = True

    views_to_test = [
        (views.HomePageView, '/', 'pages/home/home.html', {}),
        (views.NewTestView, '/new-test/', 'pages/newtest.html', {}),
        (views.RunsView, '/runs/', 'pages/runs.html', {}),
        (views.ResultsView, '/runs/123/', 'pages/results.html', {'run_id': 123}),
        (views.ReportsView, '/reports/', 'pages/reports.html', {}),
        (views.SettingsView, '/settings/', 'pages/settings.html', {}),
    ]

    for view_class, path, template_name, kwargs in views_to_test:
        try:
            request = factory.get(path)
            view = view_class.as_view()
            response = view(request, **kwargs)

            if response.status_code == 200:
                print(f"✅ {view_class.__name__:20} → Status 200 [PASS]")
                print(f"   Template: {template_name}")
            else:
                print(f"❌ {view_class.__name__:20} → Status {response.status_code} [FAIL]")
                all_passed = False

        except Exception as e:
            print(f"❌ {view_class.__name__:20} → ERROR: {e}")
            all_passed = False

        print()

    print("=" * 60)
    if all_passed:
        print("✅ All view tests passed!")
    else:
        print("❌ Some view tests failed")
    print("=" * 60)

    return all_passed

if __name__ == '__main__':
    urls_ok = test_urls()
    views_ok = test_views()

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"URL Configuration: {'✅ PASS' if urls_ok else '❌ FAIL'}")
    print(f"View Rendering:    {'✅ PASS' if views_ok else '❌ FAIL'}")
    print("=" * 60)

    sys.exit(0 if (urls_ok and views_ok) else 1)
