# Generated by Django 5.1.1 on 2024-09-24 20:42

import apikey.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='access',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(default=apikey.models.makeAccessKey, max_length=30)),
                ('name', models.CharField(max_length=10)),
                ('access', models.BooleanField(default=True)),
            ],
        ),
    ]