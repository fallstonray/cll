# Generated by Django 4.1.4 on 2024-02-08 16:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0023_contract_irrigation_inspections'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contract',
            old_name='customer',
            new_name='site_customer',
        ),
        migrations.RenameField(
            model_name='contract',
            old_name='visits',
            new_name='site_visits',
        ),
    ]