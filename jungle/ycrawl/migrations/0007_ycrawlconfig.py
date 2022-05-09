# Generated by Django 4.0.3 on 2022-04-04 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ycrawl', '0006_delete_vmactionshortcut_vmactionlog_result_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='YCrawlConfig',
            fields=[
                ('name', models.CharField(max_length=1023, primary_key=True, serialize=False)),
                ('value', models.CharField(blank=True, max_length=65535, verbose_name='Value (json as str)')),
            ],
        ),
    ]
