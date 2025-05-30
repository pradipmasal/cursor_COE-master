# Generated by Django 5.1.2 on 2025-04-09 15:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('quantity', models.IntegerField(default=0)),
                ('available', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='IssueRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('returned', 'Returned')], default='pending', max_length=20)),
                ('request_date', models.DateTimeField(auto_now_add=True)),
                ('issue_date', models.DateTimeField(blank=True, null=True)),
                ('return_date', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('admin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admin_requests', to=settings.AUTH_USER_MODEL)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.component')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_admin', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
