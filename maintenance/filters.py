import django_filters
from django_filters import DateFilter, CharFilter
from .models import *
from visits.models import Visit


class ContractFilter(django_filters.FilterSet):
    # start_date = DateFilter(field_name="date_created", lookup_expr='gte')
    # end_date = DateFilter(field_name="date_created", lookup_expr='lte')
    name = CharFilter(field_name='site_name', lookup_expr='icontains')

    class Meta:
        model = Contract
        fields = ['name']
        # fields = ['__all__']   # all fields
        # exclude = ['customer', 'date_created']


class CustomerFilter(django_filters.FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Customer
        fields = ['name']
        # exclude = ['customer', 'date_created']

# Each app requires its own filters.py
# Lesson learned :)
# class VisitsFilter(django_filters.FilterSet):
#     class Meta:
#         model = Visit
#         fields = '__all__'
