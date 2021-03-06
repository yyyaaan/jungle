# Jungle is from Django

A conventional implementation of Django using unit-test. See sh file for some useful commands.

To set up a new model and its database, go to `settings.py` to INATALLED_APPS, and then perform makemigrations. If folder strucuted different use full path to the automatically generated AppConfig class under `apps.py`.

> On Mac with Apple Silicon, only conda environment supported. Venv is not working for tensorflow/keras models.

## Settings outline
|||
|---|---|
|Evnironment|`python3 venv`, variable set in activat script|
|Database|Default `sqlite`, locally served, not compatible with AppEngine|
|Unit test| Using `TestCase` class with default test db|
|Timezone| currently UTC, all date ussing `django.utils.timezone`|
|Namespace|Follow Django suggestion; plug-n-paly; appname/static_or_template/appname/filename|
|Templates| Admin and rest_framework in root, all others follow namespace|
|Frontend| only views (urls, apps), model is imported from other modules|
|URL management| App-by-app in each `app/urls.py`|
|Fixtures| Initial data are saved to fixtures.json in single file|
|API Token | Only admin can generate; Bearer settings in jungle|
|Permissions | Default is IsAuthenticated, but explicited expressed everywhere|
|2FA| Admin-site enforced OTP authenticator |
|Logger| App-centralized config in `models.py` under each module |
|Cron Job| App-by-app `django-extension` ; crontab need to add manually| 

Single action is performed in `xxActionSerializer` class; job action group is done in `views(APIView)`. Common libraries are limited and organized in major user-module. Shared things under root (jungle/jungle).

## Special Usage

clean db and sink function in `models.py`

> to redo dataprocessing:  update JobControll + run check-in for today or or post a check in with offset (int) to force dataprocessing

> to force a checkin, go to checkin and parse the keyword

## Deployment checklist

- Environment variable for Django and Gcloud
- OTP token, service token etc.
- SSH cert is a must to use Token Auth
- Compute Vision Models
