"""
Data migration: create Maintenance and Landscape auth Groups with
their allowed permissions.

  Maintenance — can manage contracts, customers, visits; view employees.
                No delete access. No landscape access.

  Landscape   — can manage bids, change orders, log entries, customers;
                view employees. No delete access. No maintenance access.

Delete permissions are intentionally excluded from both groups so that
only superusers (Admin) can delete records.

NOTE: If you are running this on a brand-new database, Django's
post_migrate signal may not have created Permission rows yet.
Run `python manage.py migrate` twice, or call
`python manage.py create_permissions` after the first run.
"""
from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    maintenance_group, _ = Group.objects.get_or_create(name='Maintenance')
    landscape_group, _ = Group.objects.get_or_create(name='Landscape')

    def get_perm(app_label, codename):
        try:
            return Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
        except Permission.DoesNotExist:
            return None

    # --- Maintenance group ---
    maint_pairs = [
        # Maintenance contracts
        ('maintenance', 'view_contract'),
        ('maintenance', 'add_contract'),
        ('maintenance', 'change_contract'),
        # Customers (shared with Landscape)
        ('maintenance', 'view_customer'),
        ('maintenance', 'add_customer'),
        ('maintenance', 'change_customer'),
        # Visits
        ('visits', 'view_visit'),
        ('visits', 'add_visit'),
        ('visits', 'change_visit'),
        # Employees — view only
        ('employee', 'view_employee'),
    ]
    maint_perms = [p for p in (get_perm(a, c) for a, c in maint_pairs) if p]
    maintenance_group.permissions.set(maint_perms)

    # --- Landscape group ---
    land_pairs = [
        # Bids / projects
        ('landscape', 'view_bid'),
        ('landscape', 'add_bid'),
        ('landscape', 'change_bid'),
        # Change orders
        ('landscape', 'view_changeorder'),
        ('landscape', 'add_changeorder'),
        ('landscape', 'change_changeorder'),
        # Daily log entries
        ('landscape', 'view_dailylogentry'),
        ('landscape', 'add_dailylogentry'),
        ('landscape', 'change_dailylogentry'),
        # Customers (shared with Maintenance)
        ('maintenance', 'view_customer'),
        ('maintenance', 'add_customer'),
        ('maintenance', 'change_customer'),
        # Employees — view only
        ('employee', 'view_employee'),
    ]
    land_perms = [p for p in (get_perm(a, c) for a, c in land_pairs) if p]
    landscape_group.permissions.set(land_perms)


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Maintenance', 'Landscape']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('landscape', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
