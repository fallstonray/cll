from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Visit
from maintenance.models import Contract, Customer


class VisitForm(ModelForm):
    class Meta:
        model = Visit
        fields = '__all__'
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the dropdown for contract is alphabetically ordered
        self.fields['visit_contract'].queryset = Contract.objects.order_by('site_name')  
        # Replace 'name' with the actual field you want to order by