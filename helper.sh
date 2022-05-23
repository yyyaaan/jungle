source ./.venv/bin/activate

# delete all packages (to reinstall later)
pip freeze | xargs pip uninstall -y

# create project, app
django-admin startproject jungle
python manage.py startapp appname

# create super user, generally only for testing
python manage.py createsuperuser
python manage.py addstatictoken myusername

# database  and unit testing
python manage.py makemigrations appname
python manage.py migrate
python manage.py test appname

# django-extensions https://django-extensions.readthedocs.io/en/latest/command_extensions.html
python manage.py create_jobs appname
python ./jungle/manage.py runjobs hourly


# save current data to fixtures, for future loaddata
python ./jungle/manage.py dumpdata ycrawl > xxx.json
python ./jungle/manage.py runserver

rm -f ./jungle/media/vision/*