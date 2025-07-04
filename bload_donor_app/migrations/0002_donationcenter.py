# Generated by Django 5.2.1 on 2025-06-04 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bload_donor_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DonationCenter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('location', models.CharField(blank=True, max_length=200, null=True)),
                ('contact_person', models.CharField(blank=True, max_length=100, null=True)),
                ('phone', models.CharField(blank=True, max_length=13, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('operating_hours', models.CharField(help_text='e.g. Mon-Fri, 9AM–5PM', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
    ]
