# Generated by Django 5.1.1 on 2024-09-23 00:25

import django.db.models.deletion
import repo.models
import traffic.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='node',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backend', models.CharField(default='XUI', max_length=10)),
                ('address', models.CharField(max_length=50)),
                ('auth', models.CharField(max_length=100)),
                ('host', models.CharField(max_length=30)),
                ('max_traffic', traffic.fields.TrafficField()),
                ('period', models.DurationField()),
                ('period_start', models.DateField()),
                ('settings', models.CharField(max_length=100)),
                ('enable', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
                ('node_number', models.IntegerField()),
                ('connection_number', models.IntegerField(default=1)),
                ('period', models.DurationField()),
                ('traffic', traffic.fields.TrafficField()),
            ],
        ),
        migrations.CreateModel(
            name='subscribe',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('api_pk', models.CharField(max_length=20)),
                ('view_pk', models.CharField(max_length=20)),
                ('node_number', models.IntegerField()),
                ('connection_number', models.IntegerField()),
                ('period', models.DurationField()),
                ('traffic', traffic.fields.TrafficField()),
                ('start_date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='assign',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('enable', models.BooleanField(default=True)),
                ('uuid', models.CharField(max_length=20)),
                ('node', models.ForeignKey(on_delete=repo.models.assign_on_node_delete, to='repo.node')),
                ('subscribe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='repo.subscribe')),
            ],
        ),
    ]
