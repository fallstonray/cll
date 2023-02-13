import django_filters
from .models import *
from django_filters import DateFilter


class VisitsFilter(django_filters.FilterSet):
    class Meta:
        model = Visit
        fields = '__all__'
        exclude = ['notes', 'total_man_hours', 'crew_size']
