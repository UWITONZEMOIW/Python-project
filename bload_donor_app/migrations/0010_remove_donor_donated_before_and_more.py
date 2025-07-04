# Generated by Django 5.2.1 on 2025-06-19 10:48

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bload_donor_app', '0009_collector_last_login_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='donor',
            name='donated_before',
        ),
        migrations.RemoveField(
            model_name='donor',
            name='last_donation',
        ),
        migrations.AddField(
            model_name='donationappointment',
            name='has_donated_before',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='collector',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='collector',
            name='username',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='donationappointment',
            name='appointment_date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='donationappointment',
            name='appointment_time',
            field=models.TimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='donationappointment',
            name='collector',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bload_donor_app.collector'),
        ),
        migrations.AlterField(
            model_name='donationappointment',
            name='donor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointments', to='bload_donor_app.donor'),
        ),
        migrations.AlterField(
            model_name='donationappointment',
            name='selected_center',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
    ]
