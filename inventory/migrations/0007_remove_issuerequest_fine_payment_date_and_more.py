# Generated by Django 5.2 on 2025-04-26 18:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_issuerequest_fine_amount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issuerequest',
            name='fine_payment_date',
        ),
        migrations.RemoveField(
            model_name='issuerequest',
            name='fine_payment_method',
        ),
        migrations.RemoveField(
            model_name='issuerequest',
            name='fine_payment_reference',
        ),
        migrations.RemoveField(
            model_name='issuerequest',
            name='fine_payment_status',
        ),
    ]
