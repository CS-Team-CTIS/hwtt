# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HWTT (Hardware Test Tracker) is a Django 6.0 web application for managing hardware rut-depth testing workflows. It tracks test runs, measurements, results, and artifacts for specimens tested with a wheel-tracking apparatus. Uses Python 3.14, SQLite, Tailwind CSS 4, and django-htmx.

## Commands

### Development server
```bash
python manage.py runserver
```

### Tailwind CSS (from `hwtt/theme/`)
```bash
npm run dev    # watch mode, outputs to hwtt/static/css/tailwind.css
npm run build  # production minified build
```

### Database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Tests
```bash
python manage.py test              # Django test runner
python manage.py test core         # Run tests for the core app only
python test_routing.py             # Standalone URL routing + view rendering tests
```

## Architecture

### Django project structure
- **`hwtt/`** — Django project package (settings, root URLs, WSGI/ASGI, static files, Tailwind theme)
- **`core/`** — Single Django app containing all models, views, URLs, and admin config
- **`templates/`** — Project-level templates directory (not inside any app)

### URL routing
Root URLs (`hwtt/urls.py`) include admin and delegate everything else to `core/urls.py` (namespaced as `core`). All views are class-based (`django.views.View`). Use `core:<name>` for URL reversal (e.g., `core:home`, `core:results` with `run_id` kwarg).

### Data model hierarchy
`TestRun` is the central model. Relationships flow downward:
- **TestRun** → **TestResults** (FK, `related_name='results'`)
- **TestRun** → **TestMeasurements** (FK, `related_name='measurements'`) — individual pass/rut-depth data points
- **TestResults** → **TestArtifacts** (FK, `related_name='artifacts'`)

Status and rating enums are `IntegerChoices` defined in `core/models.py` (`StatusMapping`, `RatingClassificationMapping`).

### Templates
All templates extend `templates/layout.html` which provides the nav bar and content block. Page templates live in `templates/pages/`. The layout loads `static/css/tailwind.css`.

### Tailwind CSS setup
Tailwind v4 is configured in `hwtt/theme/` with its own `package.json`. The config (`hwtt/theme/tailwind.config.js`) scans `templates/**/*.html` for class usage. Source CSS is at `hwtt/theme/src/input.css`, output goes to `hwtt/static/css/tailwind.css`. Custom theme colors: `primary` (#2a3d56) and `accent` (#e4925d).

### Static files
`STATICFILES_DIRS` points to `hwtt/static/`. The compiled Tailwind CSS is the main static asset.
