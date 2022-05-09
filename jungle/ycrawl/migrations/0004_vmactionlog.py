# Generated by Django 4.0.3 on 2022-03-28 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ycrawl', '0003_vmtrail_id_alter_vmtrail_vmid'),
    ]

    operations = [
        migrations.CreateModel(
            name='VmActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(max_length=1023, verbose_name='Event description')),
                ('info', models.CharField(blank=True, max_length=9999, verbose_name='Information')),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('vmids', models.ManyToManyField(to='ycrawl.vmregistry')),
            ],
        ),
    ]
