from django.db import models
from phone_field import PhoneField
# Create your models here.


class Employee(models.Model):
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    work_phone = PhoneField(E164_only=False, blank=True, null=True)
    personal_phone = PhoneField(E164_only=False, blank=True, null=True)
    license_state = models.CharField(max_length=2, default="MD")
    license = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)
