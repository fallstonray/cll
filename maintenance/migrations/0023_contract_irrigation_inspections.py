# Generated by Django 4.1.4 on 2023-02-09 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0022_contract_tree_rings'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='irrigation_inspections',
            field=models.IntegerField(default=0, null=True),
        ),
    ]