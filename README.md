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
|Templates| Admin and rest_framework in root, all others follow namespace|
|URL management| App-by-app in each `app/urls.py`|
|Fixtures| Initial data are saved to fixtures.json in single file|
|API Token | Only admin can generate; Bearer set in root|
|Permissions | Default is IsAuthenticated, but explicited expressed everywhere|
|2FA| Admin-site enforced OTP authenticator |
|Logger| App-centralized config in `models.py` under each module |
|Cron Job| Not managed in Django; single `cronjobs.py` is to be used for cron|

Actions are performed in `xxActionSerializer` class.


## Deployment checklist

- Environment variable for Django Secret
- yCrawl database
- OTP token, service token etc.
- SSH cert is a must to use Token Auth
- Log settings config level