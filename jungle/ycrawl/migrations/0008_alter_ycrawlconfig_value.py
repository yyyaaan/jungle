# Generated by Django 4.0.3 on 2022-04-05 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ycrawl', '0007_ycrawlconfig'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ycrawlconfig',
            name='value',
            field=models.TextField(blank=True, max_length=65535, verbose_name='Value (json as str)'),
        ),
    ]
