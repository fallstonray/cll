from django.db import models
from phone_field import PhoneField
# Create your models here.


class Position(models.Model):
    employee_title = models.CharField(max_length=12)

    def __str__(self):
        return self.employee_title


class Employee(models.Model):
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    employee_title = models.ForeignKey(
        Position, null=True, on_delete=models.SET_NULL)
    work_phone = PhoneField(E164_only=False, blank=True, null=True)
    personal_phone = PhoneField(E164_only=False, blank=True, null=True)
    license_state = models.CharField(max_length=2, default="MD")
    license = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)
