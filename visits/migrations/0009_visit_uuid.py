import uuid
from django.db import migrations, models


def gen_uuid(apps, schema_editor):
    Visit = apps.get_model('visits', 'Visit')
    for row in Visit.objects.all():
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0008_remove_visit_visit_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(gen_uuid, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='visit',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
