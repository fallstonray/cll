from django.db import models
from datetime import date, datetime
from django.utils import timezone


class VisitType(models.Model):
    visit_type_name = models.CharField(max_length=120)

    def __str__(self):
        return self.visit_type_name


class Visit(models.Model):
    visit_type_name = models.ForeignKey(
        'VisitType', null=True, on_delete=models.SET_NULL)
    contract = models.ForeignKey(
        'maintenance.Contract', null=True, on_delete=models.SET_NULL)
    visit_date = models.DateField(
        default=date.today, null=True, blank=True)
    crewsize = models.CharField(max_length=128, blank=False)
    total_man_hours = models.FloatField(blank=False)
    notes = models.CharField(max_length=1024, null=True, blank=True)
    # created_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.contract)
