from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Visit
from maintenance.models import Contract, Customer


class VisitForm(ModelForm):
    class Meta:
        model = Visit
        fields = '__all__'
