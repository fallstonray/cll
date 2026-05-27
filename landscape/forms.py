from django.forms import ModelForm, DateInput
from .models import Bid, ChangeOrder, DailyLogEntry
from employee.models import Employee
from maintenance.models import Customer


class BidForm(ModelForm):
    """Create form — streamlined fields only. Hides project/warranty fields."""
    class Meta:
        model = Bid
        exclude = [
            'uuid', 'created_at',
            'start_date', 'end_date',
            'contract_signed', 'warranty_days',
            'follow_up_notes', 'status',
        ]
        widgets = {
            'bid_submitted':  DateInput(attrs={'type': 'date'}),
            'last_contact':   DateInput(attrs={'type': 'date'}),
            'next_follow_up': DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'location': 'Address / Street',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(
            is_general_contractor=True).order_by('name')
        self.fields['estimator'].queryset = Employee.objects.filter(
            is_active=True, is_office_staff=True).order_by('last_name')


class BidUpdateForm(ModelForm):
    """Update form — all fields, used once a bid exists."""
    class Meta:
        model = Bid
        exclude = ['uuid', 'created_at']
        widgets = {
            'bid_submitted':  DateInput(attrs={'type': 'date'}),
            'last_contact':   DateInput(attrs={'type': 'date'}),
            'next_follow_up': DateInput(attrs={'type': 'date'}),
            'start_date':     DateInput(attrs={'type': 'date'}),
            'end_date':       DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'location': 'Address / Street',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(
            is_general_contractor=True).order_by('name')
        self.fields['estimator'].queryset = Employee.objects.filter(
            is_active=True, is_office_staff=True).order_by('last_name')


class ChangeOrderForm(ModelForm):
    class Meta:
        model = ChangeOrder
        fields = '__all__'
        exclude = ['uuid', 'created_at', 'bid']
        widgets = {
            'date_submitted': DateInput(attrs={'type': 'date'}),
        }


class DailyLogEntryForm(ModelForm):
    class Meta:
        model = DailyLogEntry
        fields = ['date', 'entry']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }
