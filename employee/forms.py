from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Employee
from maintenance.models import Contract, Customer
from visits.models import Visit, VisitType


class EmployeeForm(ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
