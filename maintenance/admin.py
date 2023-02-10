from django.contrib import admin
from .models import *
from visits.models import Visit, VisitType
from employee.models import Employee, Position

# Models for main app 'maintenance'

admin.site.register(Customer)
admin.site.register(Contract)
admin.site.register(Soldby)
admin.site.register(Mulchcolor)


# Models for 2nd app 'visits'
admin.site.register(Visit)
admin.site.register(VisitType)

# Models for 3rd app 'employee'
admin.site.register(Employee)
admin.site.register(Position)
