source ./.venv/bin/activate

# create project, app
django-admin startproject jungle
python manage.py startapp play

# create super user, generally only for testing
python manage.py createsuperuser
python manage.py addstatictoken myusername


# database  and unit testing
python manage.py makemigrations appname
python manage.py migrate
python manage.py test appname

# save current data to fixtures, for future loaddata
python ./jungle/manage.py dumpdata ycrawl > xxx.json

python ./jungle/manage.py runserver
