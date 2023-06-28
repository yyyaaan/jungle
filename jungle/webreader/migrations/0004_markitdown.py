# Generated by Django 4.0.4 on 2022-06-27 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webreader', '0003_alter_webreader_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkItDown',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('md', models.TextField(blank=True, max_length=1048576, verbose_name='markdown')),
                ('enabled', models.BooleanField(verbose_name='Show?')),
            ],
        ),
    ]