# Generated by Django 4.1.4 on 2023-01-27 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0014_mulchcolor_rename_salesman_contract_salesrep_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='irrigation',
            field=models.BooleanField(default=False),
        ),
    ]
