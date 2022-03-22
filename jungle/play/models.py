from django.db import models
from django.utils import timezone
from datetime import timedelta

from sympy import timed

# Create your models here.
class Question(models.Model):
    q_text = models.CharField("question text", max_length=999)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.q_text

    def is_recent(self):
        return self.pub_date >= (timezone.now() - timedelta(days=1))

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField("choice text", max_length=999)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
