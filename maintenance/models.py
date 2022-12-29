from django.db import models
from phone_field import PhoneField
from datetime import date



class Customer(models.Model):
    name = models.CharField(max_length=128, null=True)
    add1 = models.CharField(max_length=128, null=True)
    add2 = models.CharField(max_length=128, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, default="Baltimore")
    state = models.CharField(max_length=2, null=True, default="MD")
    zip = models.CharField(max_length=5, null=True, default="21220")
    contact_name = models.CharField(max_length=100, null=True)
    phone1 = PhoneField(E164_only=False, blank=True, null=True)
    phone2 = PhoneField(blank=True, null=True)
    email = models.EmailField(max_length=254, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    notes = models.CharField(max_length=1024, null=True, blank=True)
    billing_name = models.CharField(max_length=128, blank=True, null=True)
    billing_add1 = models.CharField(max_length=128, blank=True, null=True)
    billing_add2 = models.CharField(max_length=128, blank=True, null=True)
    billing_city = models.CharField(max_length=128, blank=True, null=True)
    billing_state = models.CharField(max_length=2, blank=True, null=True)
    billing_zip = models.CharField(max_length=5, blank=True, null=True)
    billing_ref = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name


class Soldby(models.Model):
    salesman = models.CharField(max_length=20, null=True)

    def __str__(self):
        return self.salesman


class Contract(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField()
    visits = models.IntegerField(default=24)
    price = models.FloatField(null=True)
    customer = models.ForeignKey(
        Customer, null=True, on_delete=models.SET_NULL)
    salesman = models.ForeignKey(Soldby, null=True, on_delete=models.SET_NULL)
    notes = models.CharField(max_length=1024, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name
