import uuid
from django.db import migrations, models


def gen_uuid(apps, schema_editor):
    Employee = apps.get_model('employee', 'Employee')
    for row in Employee.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0004_employee_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(gen_uuid, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='employee',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
