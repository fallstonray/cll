from django.forms import ModelForm
from .models import Contract, Customer
#test comment :)

class ContractForm(ModelForm):
    class Meta:
        model = Contract
        fields = '__all__'


class CustomerForm(ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
