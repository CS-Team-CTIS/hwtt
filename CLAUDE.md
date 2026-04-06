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
- **`core/`** — Single Django app containing all models, views, forms, services, URLs, and admin config
- **`templates/`** — Project-level templates directory (not inside any app)

### URL routing
Root URLs (`hwtt/urls.py`) include admin, serve media files in debug mode, and delegate everything else to `core/urls.py` (namespaced as `core`). Auth views (login, logout, signup) are defined in `core/urls.py` alongside app views. Use `core:<name>` for URL reversal (e.g., `core:home`, `core:results` with `run_id` kwarg, `core:binder_grade_create`).

### Data model hierarchy
`TestRun` is the central model. Relationships flow downward:
- **BinderGrade** — reference data for binder types (name, max_rut, passes_to_rut). Referenced by TestRun via FK.
- **TestRun** → **TestResults** (FK, `related_name='results'`)
- **TestRun** → **TestMeasurements** (FK, `related_name='measurements'`) — individual pass/rut-depth data points
- **TestResults** → **TestArtifacts** (FK, `related_name='artifacts'`) — reports, logs, images, videos

Enums are `IntegerChoices` in `core/models.py`: `TestRunStatus` (PENDING/RUNNING/COMPLETED/FAILED), `RatingClassification` (EXCELLENT/GOOD/FAIR/POOR), `TestFileType` (INSTROTEK/TROXLER/PTI/CUSTOM).

### Services layer (`core/services.py`)
Business logic lives in service classes, not views:
- **ValidateFileService** — detects file encoding, parses CSV files by type (Instrotek INI-style, Custom auto-detect; Troxler and PTI are stubs). Returns shape, headers, and validity for HTMX preview.
- **AnalysisRunService** — runs the analysis pipeline: loads dataframe, creates TestResults with rut depths at key cycle counts (5k/10k/15k/20k/final), calculates the Stripping Inflection Pass (SIP), generates Plotly chart JSON, and updates TestRun status.

### Templates
All templates extend `templates/layout.html` which provides the nav bar, HTMX 2.0.4, and Plotly 3.3.0. Page templates live in `templates/pages/`. Reusable HTMX-swappable fragments live in `templates/partials/` (runs table, file preview, binder grade form/rows, chart).

### HTMX patterns
- **Prefer HTMX over raw JavaScript.** Use HTMX attributes and server-rendered partials for all dynamic UI behavior (form interactions, live updates, conditional fields). Only use JS for purely client-side concerns (e.g., dropzone click-to-open).
- Partial page updates: views check for `?partial=table` or HTMX headers and return only the relevant partial template instead of the full page.
- Out-of-band swaps (`hx-swap-oob`) for updating multiple DOM regions in a single response (e.g., binder grade table + form placeholder).
- File validation triggers on file input change, swaps preview into `#parse-preview`.

### Tailwind CSS setup
Tailwind v4 is configured in `hwtt/theme/` with its own `package.json`. The config (`hwtt/theme/tailwind.config.js`) scans `templates/**/*.html` for class usage. Source CSS is at `hwtt/theme/src/input.css`, output goes to `hwtt/static/css/tailwind.css`. Custom theme colors: `primary` (#2a3d56, with `-dark` and `-light` variants) and `accent` (#e4925d, with variants).

### Static and media files
- `STATICFILES_DIRS` points to `hwtt/static/`. The compiled Tailwind CSS is the main static asset.
- `MEDIA_ROOT` is `media/` at project root; uploaded test data files are stored here. Media is served via `static()` helper in debug mode.

### Authentication
All views use `LoginRequiredMixin`. Auth redirects: `LOGIN_URL=/login`, `LOGIN_REDIRECT_URL=/home`, `LOGOUT_REDIRECT_URL=/login`.

### Custom settings
`ANALYSIS_VERSION` in `hwtt/settings.py` tracks the analysis algorithm version — increment when changing analysis logic in services.
