# Generated by Django 4.1.4 on 2023-02-06 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0018_alter_contract_end_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='mulch_fall',
            field=models.BooleanField(default=False),
        ),
    ]
