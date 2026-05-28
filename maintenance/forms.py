from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Contract, Customer


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ContractForm(ModelForm):
    class Meta:
        model = Contract
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'})
        }
        

class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'contact_name', 'phone1', 'phone2', 'email', 'notes', 'is_general_contractor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact_name'].required = False
