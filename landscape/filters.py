import django_filters
from django_filters import CharFilter, ModelChoiceFilter
from .models import Bid
from employee.models import Employee
from maintenance.models import Customer


class BidFilter(django_filters.FilterSet):
    project_name = CharFilter(
        field_name='project_name',
        lookup_expr='icontains',
        label='Project Name',
    )
    state = CharFilter(
        field_name='state',
        lookup_expr='iexact',
        label='State',
    )
    estimator = ModelChoiceFilter(
        queryset=Employee.objects.filter(is_active=True, is_office_staff=True).order_by('last_name'),
        label='Estimator',
    )
    customer = ModelChoiceFilter(
        queryset=Customer.objects.filter(is_general_contractor=True).order_by('name'),
        label='Customer / GC',
    )

    class Meta:
        model = Bid
        fields = ['project_name', 'state', 'phase', 'estimator', 'customer']
