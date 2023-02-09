from django.db import models
from datetime import date


class VisitType(models.Model):
    visit_type = models.CharField(max_length=20, blank=False)

    def __str__(self):
        return self.visit_type


class Visit(models.Model):
    visit_type = models.ForeignKey(
        'visitType', null=True, on_delete=models.SET_NULL)
    contract = models.ForeignKey(
        'maintenance.Contract', null=True, on_delete=models.SET_NULL)
    visit_date = models.DateField(default=date.today)
    crewsize = models.CharField(max_length=128, blank=False)
    total_man_hours = models.IntegerField(blank=False)
    notes = models.CharField(max_length=1024, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.visit_type
