import uuid
from django.db import migrations, models


def gen_uuid_contract(apps, schema_editor):
    Contract = apps.get_model('maintenance', 'Contract')
    for row in Contract.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])


def gen_uuid_customer(apps, schema_editor):
    Customer = apps.get_model('maintenance', 'Customer')
    for row in Customer.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0025_contract_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='customer',
            name='uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(gen_uuid_contract, migrations.RunPython.noop),
        migrations.RunPython(gen_uuid_customer, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contract',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
