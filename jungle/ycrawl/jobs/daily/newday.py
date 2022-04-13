from django_extensions.management.jobs import DailyJob
from types import SimpleNamespace

from ycrawl.views import StartYcrawl

class Job(DailyJob):

    def execute(self):
        StartYcrawl().post(
            request=SimpleNamespace(data={"stop": 1}),
            format="CRON"
        )
        