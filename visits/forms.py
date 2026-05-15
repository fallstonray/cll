from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Visit
from maintenance.models import Contract, Customer
from employee.models import Employee


class VisitForm(ModelForm):
    class Meta:
        model = Visit
        fields = '__all__'
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['visit_contract'].queryset = Contract.objects.filter(is_active=True).order_by('site_name')
        self.fields['crew_leader'].queryset = Employee.objects.filter(is_active=True).order_by('last_name')