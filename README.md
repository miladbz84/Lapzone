# Lapzone

Lapzone is a Persian, right-to-left laptop storefront built with Python and Django. It provides product browsing, category pages, search, a session-based cart, and customer account pages.

## Features

- Browse product categories, product details, images, stock, and prices.
- Search products by name or description.
- Add items to a session cart, update quantities, remove items, and view current database prices.
- Register, sign in, update a profile, and change a password.
- Manage categories, products, and product images through Django Admin.
- Persian RTL interface and local product image uploads.

## Technology

- Python 3.10+
- Django 5.2.6
- SQLite (Django default database)
- Pillow 11.3.0 for image fields
- Django templates, HTML, CSS, and small template-embedded JavaScript interactions

## Project layout

```text
Lapzone/
├── manage.py
├── Lapzone/                 # Django settings and project URL configuration
├── store/                   # Store views, models, forms, admin, and migrations
│   ├── migrations/
│   ├── static/               # Store CSS and admin styling
│   └── templates/            # Store pages
├── templates/admin/          # Admin template customization
└── media/products/           # Product uploads / sample product images
```

## Setup (PowerShell)

Run commands from the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The Django project is in the `Lapzone` subdirectory. Configure environment variables for the current PowerShell session before starting it:

```powershell
$env:DJANGO_SECRET_KEY = 'replace-with-a-new-random-development-key'
$env:DJANGO_DEBUG = 'True'
$env:DJANGO_ALLOWED_HOSTS = '127.0.0.1,localhost'
Set-Location .\Lapzone
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The settings read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` directly from the process environment; this repository does not load a `.env` file. Do not commit real secrets. Use a separate, newly generated key for each environment.

For a Unix-like shell, export the same variables before running `python manage.py` from `Lapzone/`:

```sh
export DJANGO_SECRET_KEY='replace-with-a-new-random-development-key'
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'
```

## Database and admin

A fresh checkout can initialize its local SQLite database with `python manage.py migrate`. Create an administrator with `python manage.py createsuperuser`, then visit `/admin/`. Keep local database files and real user data out of public releases.

## Tests and checks

From `Lapzone/`, run the project checks with:

```sh
python manage.py check
python manage.py test
```

Tests that write data should use Django's test database. Do not point tests at a database containing real or development user records.

## Static and media files

Django discovers the app's CSS in `store/static/` through its installed-app static finder. `STATIC_ROOT` is `staticfiles/` for collected production assets. Uploaded product images use `MEDIA_ROOT` (`media/`) and `MEDIA_URL` (`/media/`). The development URL configuration serves media while `DEBUG` is enabled. Production deployments must serve collected static assets and uploaded media through an appropriate web server or storage service; Django's development server is not a production file server.

## Current limitations

Checkout currently displays the cart summary and address form. It does **not** create or persist an order, reserve stock, or process a payment. The contact page is a user-facing page; no external email delivery integration is configured. Treat these as presentation/demo flows, not a live commerce system.

## Security and publication notes

- State-changing cart and logout endpoints require POST and use Django CSRF protection.
- Cart prices and checkout totals are recalculated from current product records; any price or name cached in the session is treated as untrusted display data.
- Registration applies the configured Django password validators.
- The project defaults to `DEBUG=False` and requires `DJANGO_SECRET_KEY`; set `DJANGO_ALLOWED_HOSTS` for the deployment host. HTTPS, proxy, cookie, and HSTS settings still need to be matched to the production hosting setup.
- Repository history may contain previously committed sensitive values. Removing a file from the current snapshot does not remove old Git objects. Rotate any exposed credentials and review repository history before public release. No history rewrite or remote change is performed by this project preparation.
- Review uploaded media and all tracked files for ownership, privacy, and redistribution rights before publishing.
