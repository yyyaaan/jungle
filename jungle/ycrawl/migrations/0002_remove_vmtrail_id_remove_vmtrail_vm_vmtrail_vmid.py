# Generated by Django 4.0.3 on 2022-03-25 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ycrawl', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vmtrail',
            name='id',
        ),
        migrations.RemoveField(
            model_name='vmtrail',
            name='vm',
        ),
        migrations.AddField(
            model_name='vmtrail',
            name='vmid',
            field=models.CharField(default='a', max_length=20, primary_key=True, serialize=False, verbose_name='Assigned VMID'),
            preserve_default=False,
        ),
    ]
