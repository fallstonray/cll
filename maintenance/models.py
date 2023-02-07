from django.db import models
from phone_field import PhoneField
from datetime import date, timedelta


class Customer(models.Model):
    name = models.CharField(max_length=128, null=True)
    add1 = models.CharField(max_length=128, null=True)
    add2 = models.CharField(max_length=128, null=True, blank=True)
    city = models.CharField(max_length=128, null=True)
    state = models.CharField(max_length=2, null=True, default="MD")
    zip = models.CharField(max_length=5, null=True)
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


class Mulchcolor(models.Model):
    color = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.color


def get_end_date():
    return date.today() + timedelta(days=365)


class Contract(models.Model):
    site_name = models.CharField(max_length=200)
    customer = models.ForeignKey(
        Customer, null=True, on_delete=models.SET_NULL)
    contract_description = models.CharField(
        max_length=200, default='Maintenance Contract')
    location = models.CharField(max_length=200)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(default=get_end_date)
    price = models.FloatField(null=True)
    payments = models.IntegerField(default=12, null=True)
    salesrep = models.ForeignKey(Soldby, null=True, on_delete=models.SET_NULL)
    notes = models.CharField(max_length=1024, null=True, blank=True)

    visits = models.IntegerField(default=24, null=True)
    sq_turf = models.IntegerField(default=0, null=True)
    sq_mulch = models.IntegerField(default=0, null=True)
    hours_total_contract = models.IntegerField(null=True)

    mulch_yd = models.IntegerField(default=0, null=True)
    mulch_color = models.ForeignKey(
        Mulchcolor, null=True, blank=True, on_delete=models.SET_NULL)
    mulch_fall = models.BooleanField(default=False)

    leaf_cleanup = models.SmallIntegerField(default=1, null=True)
    aeration_overseed = models.BooleanField(default=False)
    turf_apps = models.BooleanField(default=False)
    turf_apps_count = models.IntegerField(default=0, null=True)
    irrigation = models.BooleanField(default=False)

    flowers_spring = models.IntegerField(default=0, null=True)
    flowers_fall = models.IntegerField(default=0, null=True)

    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.site_name
