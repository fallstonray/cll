import django_filters
from django_filters import DateFilter, CharFilter
from .models import *


class ContractFilter(django_filters.FilterSet):
    # start_date = DateFilter(field_name="date_created", lookup_expr='gte')
    # end_date = DateFilter(field_name="date_created", lookup_expr='lte')
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Contract
        fields = ['name']
        # exclude = ['customer', 'date_created']


class CustomerFilter(django_filters.FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Customer
        fields = ['name']
        # exclude = ['customer', 'date_created']
