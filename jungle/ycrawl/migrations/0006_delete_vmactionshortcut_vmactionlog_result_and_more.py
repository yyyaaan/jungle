# Generated by Django 4.0.3 on 2022-04-01 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ycrawl', '0005_vmactionshortcut'),
    ]

    operations = [
        migrations.DeleteModel(
            name='VmActionShortcut',
        ),
        migrations.AddField(
            model_name='vmactionlog',
            name='result',
            field=models.CharField(blank=True, max_length=9999, verbose_name='Action Output'),
        ),
        migrations.AlterField(
            model_name='vmtrail',
            name='event',
            field=models.CharField(max_length=1023, verbose_name='Event'),
        ),
    ]
