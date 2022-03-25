# Jungle is from Django

A conventional implementation of Django using unit-test. See sh file for some useful commands.

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
|Fixtures| Initial data are saved to fixtures.json in single file|
|API Token | Only admin can generate; Bearer set in root|
|Permissions | Default is IsAuthenticated, but explicited expressed everywhere|


## Some interesting command

`python manage.py shell` provides Jupyter-like interface to ease database management.

Migration code automatically by `python manage.py makemigrate appname`. SQL migration code is printed by `python manage.py sqlmigrate appname 0001` if DB is managed externally.

## Deployment checklist

- Environment variable for Django Secret
- User group data to be dumped and save to fixture