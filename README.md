# Jungle is from Django

A conventional implementation of Django.

```
django-admin startproject jungle
python manage.py startapp play
python manage.py runserver

# python manage.py makemigrate appname
python manage.py migrate
python manage.py createsuperuser
```

To set up a new model and its database, go to `settings.py` to INATALLED_APPS, and then perform makemigrations. If folder strucuted different use full path to the automatically generated AppConfig class under `apps.py`.

## Settings outline
|||
|---|---|
|Database|Default `sqlite`. External DBs are refered|
|URL management| App-by-app; `urls.py` under each app|
|Timezone| currently UTC, all date ussing `django.utils.timezone`


## Some interesting command

`python manage.py shell` provides Jupyter-like interface to ease database management.

Migration code automatically by `python manage.py makemigrate appname`. SQL migration code is printed by `python manage.py sqlmigrate appname 0001` if DB is managed externally.

