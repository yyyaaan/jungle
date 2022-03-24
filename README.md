# Jungle is from Django

A conventional implementation of Django using unit-test.

```
django-admin startproject jungle
python manage.py startapp play
python manage.py runserver

python manage.py makemigrations appname
python manage.py migrate

python manage.py createsuperuser

python manage.py test appname
```

To set up a new model and its database, go to `settings.py` to INATALLED_APPS, and then perform makemigrations. If folder strucuted different use full path to the automatically generated AppConfig class under `apps.py`.

## Settings outline
|||
|---|---|
|Evnironment|`python3 venv`, variable set in activat script|
|Database|Default `sqlite`, locally served, not compatible with AppEngine|
|Unit test| Using `TestCase` class with default test db|
|Timezone| currently UTC, all date ussing `django.utils.timezone`|
|Namespace|Follow Django suggestion; plug-n-paly; appname/static_or_template/appname/filename|
|URL management| App-by-app in each `app/urls.py`|



## Some interesting command

`python manage.py shell` provides Jupyter-like interface to ease database management.

Migration code automatically by `python manage.py makemigrate appname`. SQL migration code is printed by `python manage.py sqlmigrate appname 0001` if DB is managed externally.

## Deployment checklist

Environment variable for Django Secret