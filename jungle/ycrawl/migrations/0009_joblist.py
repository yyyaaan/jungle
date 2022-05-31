# Generated by Django 4.0.4 on 2022-05-30 07:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ycrawl', '0008_alter_ycrawlconfig_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobList',
            fields=[
                ('jobid', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('weburl', models.CharField(max_length=65535)),
                ('completion', models.BooleanField(default=False, verbose_name='Completed?')),
                ('note', models.CharField(blank=True, max_length=1023)),
                ('vmid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ycrawl.vmregistry')),
            ],
        ),
    ]